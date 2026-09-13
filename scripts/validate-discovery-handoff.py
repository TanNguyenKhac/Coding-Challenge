#!/usr/bin/env python3
"""Validate a discovery-handoff/v2 YAML document.

Usage:
    python scripts/validate-discovery-handoff.py <handoff-file.yaml>

Exit codes:
    0 - valid
    1 - validation errors found
    2 - usage or file error
"""

import sys
import json
from pathlib import Path

try:
    import yaml
except ImportError:
    # Fall back to reading as plain text and basic parsing
    yaml = None


def load_handoff(path: str) -> dict:
    """Load a YAML handoff file."""
    filepath = Path(path)
    if not filepath.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(2)

    content = filepath.read_text(encoding="utf-8")

    if yaml is not None:
        return yaml.safe_load(content)

    # Minimal fallback: try JSON (some handoffs may be JSON)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print(
            "ERROR: PyYAML not installed and file is not valid JSON. "
            "Install PyYAML: pip install pyyaml",
            file=sys.stderr,
        )
        sys.exit(2)


VALID_MODES = {"spike", "bounded", "architectural"}
VALID_STATUSES = {"needs-input", "ready-for-approval", "recommendation", "blocked"}
VALID_CLASSIFICATIONS = {
    "authoritative",
    "observed",
    "derived",
    "decision-required",
    "unknown",
}
VALID_PRIORITIES = {"must", "should", "could"}
VALID_SELF_REVIEW = {"passed", "failed"}
VALID_EXTERNAL_DEFAULTS = {"deny"}


def validate(doc: dict) -> list[str]:
    """Return a list of validation error messages."""
    errors: list[str] = []

    def require(field: str, valid_set: set | None = None) -> object:
        val = doc.get(field)
        if val is None:
            errors.append(f"Missing required field: {field}")
        elif valid_set and val not in valid_set:
            errors.append(
                f"Invalid value for {field}: {val!r} "
                f"(expected one of {sorted(valid_set)})"
            )
        return val

    # Schema
    schema = doc.get("schema")
    if schema != "discovery-handoff/v2":
        errors.append(
            f"Expected schema 'discovery-handoff/v2', got {schema!r}"
        )

    # Top-level required fields
    require("change_id")
    mode = require("mode", VALID_MODES)
    status = require("status", VALID_STATUSES)

    # Repository section
    repo = doc.get("repository", {})
    if not isinstance(repo, dict):
        errors.append("'repository' must be a mapping")
        repo = {}

    repo_mode = repo.get("mode")
    if repo_mode not in ("greenfield", "brownfield", None):
        errors.append(
            f"Invalid repository.mode: {repo_mode!r} "
            "(expected 'greenfield' or 'brownfield')"
        )

    # Buildable brownfield changes need base_revision
    request = doc.get("request", {})
    requested_output = request.get("requested_output") if isinstance(request, dict) else None
    if (
        repo_mode == "brownfield"
        and requested_output == "buildable-change"
        and not repo.get("base_revision")
    ):
        errors.append(
            "base_revision is required for brownfield buildable changes"
        )

    # Evidence ledger
    ledger = doc.get("evidence_ledger", [])
    if not isinstance(ledger, list):
        errors.append("'evidence_ledger' must be a list")
        ledger = []

    evidence_ids = set()
    for i, entry in enumerate(ledger):
        if not isinstance(entry, dict):
            errors.append(f"evidence_ledger[{i}] must be a mapping")
            continue
        eid = entry.get("id")
        if not eid:
            errors.append(f"evidence_ledger[{i}] missing 'id'")
        else:
            evidence_ids.add(eid)
        classification = entry.get("classification")
        if classification and classification not in VALID_CLASSIFICATIONS:
            errors.append(
                f"evidence_ledger[{i}].classification invalid: {classification!r}"
            )

    # Requirements
    requirements = doc.get("requirements", [])
    if not isinstance(requirements, list):
        errors.append("'requirements' must be a list")
        requirements = []

    req_ids = set()
    for i, req in enumerate(requirements):
        if not isinstance(req, dict):
            errors.append(f"requirements[{i}] must be a mapping")
            continue
        rid = req.get("id")
        if not rid:
            errors.append(f"requirements[{i}] missing 'id'")
        else:
            req_ids.add(rid)
        priority = req.get("priority")
        if priority and priority not in VALID_PRIORITIES:
            errors.append(
                f"requirements[{i}].priority invalid: {priority!r}"
            )
        # Check source evidence references
        sources = req.get("source_evidence", [])
        if isinstance(sources, list):
            for ref in sources:
                if ref not in evidence_ids:
                    errors.append(
                        f"requirements[{i}].source_evidence references "
                        f"unknown evidence '{ref}'"
                    )

    # Acceptance criteria
    acs = doc.get("acceptance_criteria", [])
    if not isinstance(acs, list):
        errors.append("'acceptance_criteria' must be a list")
        acs = []

    for i, ac in enumerate(acs):
        if not isinstance(ac, dict):
            errors.append(f"acceptance_criteria[{i}] must be a mapping")
            continue
        if not ac.get("id"):
            errors.append(f"acceptance_criteria[{i}] missing 'id'")
        ac_reqs = ac.get("requirement_ids", [])
        if isinstance(ac_reqs, list):
            for ref in ac_reqs:
                if ref not in req_ids:
                    errors.append(
                        f"acceptance_criteria[{i}].requirement_ids references "
                        f"unknown requirement '{ref}'"
                    )

    # Questions
    questions = doc.get("questions", {})
    blocking = questions.get("blocking", []) if isinstance(questions, dict) else []

    # External effects
    ext = doc.get("external_effects", {})
    if isinstance(ext, dict):
        ext_default = ext.get("default")
        if ext_default and ext_default not in VALID_EXTERNAL_DEFAULTS:
            errors.append(
                f"external_effects.default must be 'deny', got {ext_default!r}"
            )

    # Self-review
    self_review = doc.get("self_review")
    if self_review and self_review not in VALID_SELF_REVIEW:
        errors.append(f"self_review invalid: {self_review!r}")

    # Status-dependent rules
    if status == "ready-for-approval":
        if blocking and len(blocking) > 0:
            errors.append(
                "status is 'ready-for-approval' but blocking questions exist"
            )
        if len(requirements) == 0:
            errors.append(
                "status is 'ready-for-approval' but no requirements defined"
            )
        if len(acs) == 0:
            errors.append(
                "status is 'ready-for-approval' but no acceptance criteria "
                "defined"
            )
        if self_review != "passed":
            errors.append(
                "self_review must be 'passed' before 'ready-for-approval'"
            )

    # Mode-dependent rules
    if mode == "architectural" and status == "ready-for-approval":
        options = doc.get("options", [])
        if not options or len(options) < 2:
            errors.append(
                "architectural mode requires at least two options for "
                "comparison"
            )
        if not doc.get("recommended_option"):
            errors.append("architectural mode requires a recommended_option")
        if not doc.get("design_refs"):
            errors.append("architectural mode requires design_refs")
        plan = doc.get("plan", {})
        if isinstance(plan, dict) and not plan.get("ref"):
            errors.append("architectural mode requires a plan ref")

    if mode == "spike":
        if doc.get("next_gate") is not None:
            errors.append("spike mode must have next_gate: null")
        if status not in ("recommendation", "blocked", "needs-input"):
            errors.append(
                f"spike mode status should be 'recommendation', 'blocked', "
                f"or 'needs-input', got {status!r}"
            )

    return errors


def main():
    if len(sys.argv) != 2:
        print(
            f"Usage: {sys.argv[0]} <handoff-file.yaml>",
            file=sys.stderr,
        )
        sys.exit(2)

    doc = load_handoff(sys.argv[1])
    if not isinstance(doc, dict):
        print("ERROR: Handoff document must be a YAML mapping", file=sys.stderr)
        sys.exit(2)

    errors = validate(doc)

    if errors:
        print(f"FAILED: {len(errors)} validation error(s):\n")
        for i, err in enumerate(errors, 1):
            print(f"  {i}. {err}")
        sys.exit(1)
    else:
        print(f"PASSED: discovery-handoff/v2 (change_id={doc.get('change_id')})")
        sys.exit(0)


if __name__ == "__main__":
    main()
