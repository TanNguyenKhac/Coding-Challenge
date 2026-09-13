---
name: sk-release-check
description: Use when a quality-verified candidate needs evidence-based delivery readiness checks for a declared demo, submission, staging, or production release profile.
---

# Release Check

Produce a defensible `ready`, `conditional`, or `blocked` verdict for delivery
readiness of a quality-verified candidate.

## Authority

- Quality verdict from `sk-quality-check` (must be pass or pass-with-observations).
- Accepted release profile and target from the discovery/verification contract.
- Repository release policy, migration plan, rollback procedure, and
  observability documentation.
- Allowed external evidence and H2 records.

## Scope

Release check evaluates delivery readiness only. It does not repeat the quality
review. Specifically, it assesses:

1. Artifact provenance and build reproducibility.
2. Target and configuration compatibility.
3. Dependency and supply-chain policy.
4. Migration and rollback readiness.
5. Observability and operator recovery.
6. Release documentation and known-risk disposition.
7. Predeclared staging or smoke evidence.

For detailed procedures per dimension, read `references/release-profiles.md` and
`references/migration-rollback-observability.md`.

## Default Boundary

Operate read-only. Do not deploy, merge, publish, perform production migration,
rotate secrets, or execute any external release action. Release check pass means
the candidate has sufficient proof for the human to choose `release` at H3; it
does not mean release has occurred.

If a runbook or manifest change is useful, propose exact hunks and wait for
approval before applying only those documentation changes.

## Procedure

1. Confirm quality verdict is pass or pass-with-observations.
2. Identify the release profile and validate it has required target, config,
   rollback, and observability documentation.
3. Review evidence for each applicable readiness dimension.
4. Execute the documented clean path when environment and authorization permit.
5. Verify setup, migrations, services, recovery steps, outputs, and checksums.
6. Classify findings by severity and readiness impact.
7. Issue a verdict with required actions and explicit limitations.

## Stop Conditions

Return `blocked` when:

- the required clean-path replay was not executed;
- a critical environment, credential, or service is unavailable;
- artifact provenance or checksum is missing;
- migration or rollback evidence required by the release contract is absent;
- a critical or high finding has no accepted disposition;
- important readiness evidence cannot be inspected.

## Verdict Rules

- `ready`: all required checks passed and no unresolved blocker remains.
- `conditional`: only disclosed limitations with authorized acceptance remain.
- `blocked`: required proof is missing or a blocker remains unresolved.

## Validation

- Never claim a check ran when it did not.
- Never call an environment clean unless setup began from the defined baseline.
- Every finding contains evidence and affected scope.
- Every required action has an owner or is explicitly unassigned.
- Repository changes respect the default read-only boundary.
