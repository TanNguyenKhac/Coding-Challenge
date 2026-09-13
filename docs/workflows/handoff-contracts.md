# Codex workflow handoff contracts

These contracts preserve state between Codex turns and agents. They are
repository artifacts, not a separate workflow runtime database.

## Discovery handoff v1

Retained for backward compatibility during migration. New discovery work should
use v2.

```yaml
schema: discovery-handoff/v1
change_id: CHG-001
status: awaiting-approval
repository_revision: "<git-sha-or-working-tree-id>"
requirements: []
acceptance_criteria: []
affected_areas: []
options: []
recommended_option: null
proposed_decisions: []
plan: null
risks: []
unknowns: []
next_gate: H1
```

At H1 the human chooses `approve`, `approve-with-conditions`, `revise`, or
`reject`. Record an approval ID, candidate repository revision, scope, and any
conditions. Implementation requires an approving decision that covers its
current scope.

## Discovery handoff v2

```yaml
schema: discovery-handoff/v2
change_id: CHG-001
mode: spike | bounded | architectural
status: needs-input | ready-for-approval | recommendation | blocked

request:
  sources: []
  requested_output: recommendation | buildable-change
  timebox_minutes: null

repository:
  mode: greenfield | brownfield
  root: null
  base_revision: null
  dirty: null

evidence_ledger:
  - id: EVD-001
    classification: authoritative | observed | derived | decision-required | unknown
    statement: ""
    source: ""

requirements:
  - id: REQ-001
    statement: ""
    source_evidence: [EVD-001]
    priority: must | should | could

acceptance_criteria:
  - id: AC-001
    requirement_ids: [REQ-001]
    observable_result: ""

scope:
  in: []
  out: []

impact:
  interfaces: []
  data_and_state: []
  modules_or_paths: []
  dependencies: []
  tests: []

questions:
  blocking: []
  non_blocking: []

assumptions: []
options: []
recommended_option: null
design_refs: []
proposed_decisions: []

plan:
  required: false
  ref: null
  work_packages: []

verification_contract:
  required_checks: []
  acceptance_matrix: []
  required_artifacts: []
  rubric_refs: []
  repeatability_policy: null
  cost_evidence_policy: null
  release_profile: none

external_effects:
  default: deny
  h2_triggers: []

risks: []
limitations: []
self_review: passed | failed
next_gate: H1 | null
```

### Validation rules

- `ready-for-approval` must not have blocking questions.
- `ready-for-approval` must have at least one requirement and one observable AC.
- `architectural` mode must have option comparison, recommendation, design ref,
  and plan ref.
- `bounded` mode may omit ADR and durable plan file.
- `spike` mode uses status `recommendation`, `next_gate: null`, and no
  implementation plan.
- Every requirement must have source evidence.
- Every in-scope requirement must have an AC and verification mapping.
- `base_revision` is required for brownfield buildable changes.
- External effects default to deny.
- `self_review: passed` is required before `ready-for-approval`.

### Mode outputs

| Field | spike | bounded | architectural |
|---|---|---|---|
| evidence_ledger | optional | required | required |
| requirements | optional | required | required |
| acceptance_criteria | optional | required | required |
| options | not required | if material tradeoff | required |
| design_refs | not required | optional | required |
| plan | not required | optional | required |
| verification_contract | not required | required | required |
| next_gate | null | H1 | H1 |

## Approval record

The same approval schema has gate-specific fields. An H1 record approves the
discovered intent and implementation scope:

```yaml
schema: approval-record/v1
approval_id: HITL-CHG-001-H1
gate: H1
change_id: CHG-001
handoff_ref: artifacts/handoffs/CHG-001-discovery.yaml
handoff_sha256: ""
base_revision: ""
decision: approve | approve-with-conditions | revise | reject
approved_scope: []
approved_option: null
conditions: []
external_effect_policy: deny
approver: ""
decided_at: ""
expires_at: null
```

`wf-implement` accepts an approval only when:

- `change_id` matches;
- handoff hash matches;
- base revision has not drifted;
- decision is `approve` or `approve-with-conditions`;
- work package scope is within approved scope.

An H2 record authorizes exactly one otherwise-denied action. It does not expand
H1 scope or authorize adjacent actions:

```yaml
schema: approval-record/v1
approval_id: HITL-CHG-001-H2-EVAL
gate: H2
change_id: CHG-001
implementation_run_id: RUN-CHG-001-01
action: "Call provider evaluation endpoint"
target: "provider-x/staging"
limits:
  max_calls: 20
  max_cost_usd: 5
rollback: "Delete the local result cache; no provider resource persists"
idempotency_key: CHG-001-EVAL-01
expires_at: "2026-09-14T00:00:00Z"
decision: approve | reject
approver: ""
decided_at: ""
```

H2 is valid only when the change and run match, the decision is `approve`, the
record is unexpired, and the action, target, limits, rollback, and idempotency
identity match the pending operation. Null, rejected, expired, or partial
matches are not approval.

## Implementation work package v2

`wf-implement` compiles approved work into dependency-aware packages. Each
agent invocation receives exactly one package.

```yaml
schema: work-package/v2
run_id: RUN-CHG-001-01
task_id: IMP-API-01
change_id: CHG-001
mode: apply | resume | fix
owner: backend-dev | ai-dev
goal: "Add idempotent request creation"
requirement_refs: [REQ-003]
acceptance_refs: [AC-003-1, AC-003-2]
decision_refs: [ADR-007]
context_refs: []
depends_on: []
allowed_paths: []
forbidden_paths: []
consumes_interfaces: []
produces_interfaces: []
test_mode: tdd | characterization | contract | verification-only | not-applicable
required_checks: []
known_baseline_failures: []
h2:
  required_for: []
stop_conditions: []
retry_limit: 2
evidence_ref: artifacts/evidence/CHG-001/IMP-API-01.json
```

Required checks must come from repository authority, CI, package scripts, or an
established validation owner. Do not invent commands. A `fix` package must also
identify its supplied verification findings in `context_refs` and may not
expand beyond them. Repository policy may override `retry_limit`, but the value
must be finite.

## Agent task result v2

An implementation agent returns a structured result; prose such as `done` is
not evidence.

```yaml
schema: agent-task-result/v2
run_id: RUN-CHG-001-01
task_id: IMP-API-01
change_id: CHG-001
owner: backend-dev
status: done | done-with-concerns | needs-context | blocked | failed
attempt: 1
base_identity: "<revision-or-content-identity>"
result_identity: "<revision-or-content-identity>"
requirement_refs: [REQ-003]
acceptance_refs: [AC-003-1, AC-003-2]
changed_paths: []
test_evidence:
  mode: tdd
  red: []
  green: []
  reason: null
checks:
  - command: "<exact-command>"
    started_at: "<rfc3339>"
    finished_at: "<rfc3339>"
    exit_code: 0
    output_summary: ""
    artifact_ref: null
self_review:
  allowed_paths: passed | failed
  acceptance_trace: passed | failed
  unrelated_changes: none | present
  sensitive_output: none | present
contract_deltas: []
external_actions: []
concerns: []
deviations: []
unresolved: []
```

For `tdd`, both `red` and `green` contain fresh command evidence and RED must
fail for the intended missing behavior before GREEN passes. Other modes record
their proof in `green`; `not-applicable` requires a reason. Every command record
contains the exact command, timestamps, exit code, and a useful output summary
or artifact reference. Evidence must be reproducible and must not contain
credentials, secrets, or sensitive payloads.

The coordinator accepts a result only after checking that the schema and status
are valid, paths remain allowed, requirement and acceptance trace is complete,
evidence matches the declared test mode, no gated action preceded H2, and the
repository state still matches the result identity. `done-with-concerns` needs
an explicit disposition before it can contribute to a passing handoff.

## Implementation progress v2

Durable runs persist their ledger outside `.harness-core/` after every state
transition:

```json
{
  "schema": "implementation-progress/v2",
  "run_id": "RUN-CHG-001-01",
  "change_id": "CHG-001",
  "mode": "apply",
  "approval_ref": "artifacts/handoffs/CHG-001/H1.json",
  "discovery_handoff_ref": "artifacts/handoffs/CHG-001/discovery-handoff.json",
  "base_revision": "abc123",
  "handoff_sha256": "sha256:...",
  "status": "in-progress",
  "retry_limit": 2,
  "tasks": [
    {
      "task_id": "IMP-API-01",
      "owner": "backend-dev",
      "status": "done",
      "attempt": 1,
      "result_identity": "def456",
      "evidence_ref": "artifacts/evidence/CHG-001/IMP-API-01.json",
      "last_error": null
    }
  ]
}
```

Workflow statuses are `in-progress`, `waiting-human`, `blocked`, `failed`,
`partial`, and `ready-for-verification`. On resume, validate the run, approval,
handoff hash, base identity, task result identity, evidence, and dependencies.
Do not redispatch a `done` task whose evidence and diff still match. Convert an
interrupted `in-progress` task to `needs-context` before deciding whether a
changed input, diagnosis, context, or strategy justifies another attempt.

## Candidate identity

A candidate must be immutable. Prefer a full commit when repository policy
permits it:

```yaml
candidate_ref:
  type: git-commit
  value: "<full-sha>"
  dirty: false
```

When the workflow may not commit, use a content manifest that hashes every
candidate path and relevant evidence:

```yaml
candidate_ref:
  type: content-manifest
  value: artifacts/evidence/CHG-001/candidate-manifest.json
  dirty: true
```

A dirty working tree without a matching content manifest is not a fixed
candidate.

## Implementation handoff v2

New implementation runs emit v2:

```yaml
schema: implementation-handoff/v2
run_id: RUN-CHG-001-01
change_id: CHG-001
mode: apply | resume | fix
approval_ref: artifacts/handoffs/CHG-001/H1.json
discovery_handoff_ref: artifacts/handoffs/CHG-001/discovery-handoff.json
base_revision: abc123
candidate_ref:
  type: git-commit | content-manifest
  value: ""
  dirty: false
status: ready-for-verification
task_results:
  - task_id: IMP-API-01
    owner: backend-dev
    skills: [sk-backend-engineering, sk-test-engineering]
    status: done
    requirement_refs: [REQ-003]
    acceptance_refs: [AC-003-1, AC-003-2]
    changed_paths: []
    evidence_ref: artifacts/evidence/CHG-001/IMP-API-01.json
contract_changes: []
external_actions: []
deviations: []
unresolved: []
checks:
  - command: "<repository-owned-command>"
    exit_code: 0
    evidence_ref: artifacts/evidence/CHG-001/final-check.json
next_workflow: wf-verify
```

Use `ready-for-verification` only when every required package is `done` or has
a valid concern disposition, required checks have fresh passing evidence, the
conformance scan finds no material `partial`, `missing`, `contradicts`, or
`unrequested-change` item, the candidate identity matches current content, and
no H2 action is pending.

## Legacy implementation handoff v1

Retained as a legacy reader format during migration. Do not emit it for a new
run.

```yaml
schema: implementation-handoff/v1
change_id: CHG-001
status: ready-for-verification
base_revision: "<git-sha-or-working-tree-id>"
candidate_revision: "<git-sha-or-working-tree-id>"
approval_id: HITL-CHG-001-H1
agents: []
skills_used: []
requirements_addressed: []
changed_files: []
test_cases: []
commands: []
artifacts: []
deviations: []
limitations: []
next_workflow: wf-verify
```

Legacy readers may consume this schema while active v1 artifacts remain. Remove
compatibility only after no active v1 consumer exists. H2 remains required
before destructive migration, production mutation, paid external call,
public-contract change outside H1, security-boundary change, significant scope
expansion, or a hard-to-reverse action.

## Verification handoff and H3

```yaml
schema: verification-handoff/v1
change_id: CHG-001
candidate_revision: "<fixed-candidate>"
verification:
  verdict: passed
  commands: []
  findings: []
  skipped_checks: []
  limitations: []
release:
  required: false
  verdict: not-evaluated
residual_risks: []
recommended_action: accept
next_gate: H3
```

Verification verdicts are `passed`, `failed`, or `blocked`. Release verdicts are
`ready`, `conditional`, `blocked`, or `not-evaluated`. H3 choices are `accept`,
`accept-with-conditions`, `return-for-fix`, `release`, or `reject`, and the
decision must identify the verified candidate revision.

Never turn a missing, interrupted, failed, malformed, or null agent result into
a passing handoff.

For each delegated task, spawn once and retain the returned agent identifier.
Use wait, inspect, message, or follow-up operations against that identifier.
Delay or temporary tool-discovery uncertainty is not permission to spawn a
duplicate agent. If the original result cannot be retrieved, report `blocked`.
