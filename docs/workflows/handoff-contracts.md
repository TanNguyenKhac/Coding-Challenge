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
handoff_ref: artifacts/handoffs/CHG-001/discovery-handoff.yaml
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
- decision is `approve` or `approve-with-conditions`;
- approval is unexpired and every recorded condition is satisfied; and
- work package scope is within approved scope.

Repository identity is mode-specific:

- `apply`: the current pre-mutation identity matches the H1 `base_revision`;
- `resume`: the current state matches the progress ledger and still-valid
  completed task identities, all rooted at the approved base; and
- `fix`: the current state matches the supplied fixed `candidate_ref`, while H1
  scope and conditions still cover the bounded findings.

A mismatch blocks before delegation. Do not weaken identity validation merely
because the original base is expected to differ after completed implementation
work.

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
authority_refs: [docs/product/change-CHG-001.md]
context_refs: []
required_skills: [sk-backend-engineering, sk-test-engineering]
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
skills: [sk-backend-engineering, sk-test-engineering]
base_identity: "<revision-or-content-identity>"
result_identity: "<revision-or-content-identity>"
requirement_refs: [REQ-003]
acceptance_refs: [AC-003-1, AC-003-2]
changed_paths: []
test_evidence:
  mode: tdd
  red: []
  green: []
  characterization: []
  contract: []
  verification: []
  reason: null
checks:
  - command: "<exact-command>"
    started_at: "<rfc3339>"
    finished_at: "<rfc3339>"
    exit_code: 0
    output_summary: ""
    artifact_ref: null
baseline_failures: []
introduced_failures: []
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
fail for the intended missing behavior before GREEN passes. Other modes use the
matching evidence list; `not-applicable` requires a reason. Baseline and
introduced failures remain separate. Every command record contains the exact
command, timestamps, exit code, and a useful output summary or artifact
reference. Evidence must be reproducible and must not contain credentials,
secrets, or sensitive payloads.

The coordinator accepts a result only after checking that the schema and status
are valid, paths remain allowed, requirement and acceptance trace is complete,
evidence matches the declared test mode, no gated action preceded H2, and the
repository state still matches the result identity. `done-with-concerns` needs
an explicit disposition before it can contribute to a passing handoff.

## Implementation progress v2

Durable runs persist their ledger outside `.harness-core/` after every state
transition:

```yaml
schema: implementation-preflight/v1
run_id: RUN-CHG-001-01
captured_at: "<rfc3339>"
repository_revision: abc123
branch_or_worktree: develop
starting_content_identity: "sha256:<digest-of-repository-path-state>"
dirty_paths:
  - path: notes/local.md
    state: present | deleted
    owner: user | implementation-run
    sha256: "sha256:<digest-or-null-when-deleted>"
    size_bytes: 1234
baseline_checks: []
```

The starting content identity covers repository-relative path, presence state,
content digest, and size in deterministic path order. Bind this snapshot by its
own digest in the progress ledger; deleted entries have null digest and size.
Pre-existing dirt defaults to user ownership; block a package whose mutable
paths overlap user-owned dirt until ownership and scope are explicitly resolved.

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
  "preflight_snapshot_ref": "artifacts/evidence/CHG-001/preflight.yaml",
  "preflight_snapshot_sha256": "sha256:...",
  "starting_content_identity": "sha256:...",
  "status": "in-progress",
  "tasks": [
    {
      "task_id": "IMP-API-01",
      "owner": "backend-dev",
      "status": "pending",
      "attempt": 0,
      "fix_round": 0,
      "retry_limit": 2,
      "agent_id": null,
      "dispatch_identity": null,
      "result_identity": null,
      "evidence_ref": "artifacts/evidence/CHG-001/IMP-API-01.json",
      "last_error": null
    }
  ],
  "external_actions": [
    {
      "action_id": "CHG-001-EVAL-01",
      "status": "waiting-human",
      "approval_ref": null,
      "approval_sha256": null,
      "action": "Call provider evaluation endpoint",
      "target": "provider-x/staging",
      "limits": {"max_calls": 20, "max_cost_usd": 5},
      "rollback": "Delete the local result cache; no provider resource persists",
      "idempotency_key": "CHG-001-EVAL-01",
      "started_at": null,
      "finished_at": null,
      "result_ref": null,
      "last_error": null
    }
  ]
}
```

Workflow statuses are `in-progress`, `waiting-human`, `blocked`, `failed`,
`partial`, and `ready-for-verification`. Progress task statuses are `pending`,
`runnable`, `in-progress`, `done`, `done-with-concerns`, `needs-context`,
`blocked`, and `failed`. External-action statuses are `planned`,
`waiting-human`, `approved`, `in-progress`, `succeeded`, `failed`, and
`uncertain`.

`attempt` counts dispatches and is zero before the first dispatch. `fix_round`
counts only retries after the initial attempt. The package's finite
`retry_limit` is copied into its progress entry and overrides no other value;
the default is two fix rounds unless repository authority supplied a different
finite package value.

Persist the action journal before requesting H2, immediately before execution,
and after observing the result. If a session stops while an action is
`in-progress` and no authoritative result is available, mark it `uncertain`.
Do not retry it until its idempotency identity and target state prove that retry
or reconciliation is safe.

On resume, validate the run, approval, handoff hash, digest-bound preflight
snapshot, starting content identity, task result identity, evidence,
dependencies, and external-action journal. Reject any unaccounted path change
or overlap with user-owned dirt. Do not redispatch a `done` task whose evidence
and diff still match. Convert an interrupted task to `needs-context` before
deciding whether a changed input, diagnosis, context, or strategy justifies
another attempt.

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
  manifest_sha256: "sha256:<digest-of-manifest-bytes>"
  dirty: true
```

The referenced manifest has a canonical shape:

```yaml
schema: candidate-manifest/v1
base_revision: abc123
created_at: "<rfc3339>"
preflight_snapshot_ref: artifacts/evidence/CHG-001/preflight.yaml
preflight_snapshot_sha256: "sha256:<digest-of-preflight-bytes>"
starting_content_identity: "sha256:<digest-of-repository-path-state>"
candidate_content_identity: "sha256:<digest-of-repository-path-state>"
files:
  - path: src/requests/service.ts
    state: present | deleted
    sha256: "sha256:<digest-of-file-bytes>"
    size_bytes: 1234
evidence:
  - path: artifacts/evidence/CHG-001/final-check.json
    sha256: "sha256:<digest-of-file-bytes>"
    size_bytes: 567
```

Represent a rename as one `deleted` old path and one `present` new path; deleted
entries have null digest and size. Sort entries by repository-relative path.
The `files` path set must exactly equal the implementation-owned path delta
between the digest-bound preflight snapshot and candidate: no changed, added,
renamed, or deleted path may be omitted, and no user-owned dirty path may
overlap. A verifier recomputes `manifest_sha256`, both repository content
identities, and every applicable entry digest and size. A dirty working tree
without a matching, digest-bound manifest is not a fixed candidate.

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
  type: git-commit
  value: def456
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
concern_dispositions: []
conformance:
  approved_intents:
    - intent_ref: AC-003-1
      status: satisfied
      evidence_refs: []
  unrequested_changes: []
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

A nonempty concern disposition records `task_id`, `concern_ref`, disposition
(`resolved` or `accepted-non-material`), `authority_ref`, and `evidence_ref`.
Approved-intent conformance status may be `satisfied`, `partial`, `missing`, or
`contradicts`. A nonempty unrequested-change entry records `change_ref`,
materiality (`material` or `non-material`), disposition (`removed` or
`authority-backed-accepted`), `authority_ref`, and `evidence_refs`.

Use `ready-for-verification` only when every required package is `done` or has
a `resolved` or authority-backed `accepted-non-material` concern disposition,
required checks have fresh passing evidence, every required intent is
`satisfied`, and every unrequested change was removed or is explicitly
non-material with an authority-backed acceptance. Any `partial`, `missing`,
`contradicts`, material unrequested change, unmatched candidate identity, or
pending/uncertain H2 action prevents readiness.

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

## Verification plan v2

The workflow compiles a finite verification plan from the approved contract
before dispatching the reviewer.

```yaml
schema: verification-plan/v2
verification_run_id: VER-CHG-001-01
change_id: CHG-001
candidate_lock:
  type: git-commit | content-manifest
  value: "<full-sha-or-sha256>"
  base_revision: "<full-sha>"
  tracked_state_clean: true
  manifest_ref: null
release_required: false
release_profile: none
dimensions: [completeness, correctness, coherence]
checks:
  - check_id: CHK-AC-001
    claim_refs: [AC-001]
    kind: automated-test | static-analysis | unit-test | contract-test | integration-test | browser-e2e | manual-observation | artifact-inspection | security-scan | performance-probe | ai-evaluation | release-readiness
    command: "<repository-owned command>"
    environment: local-isolated | ci | trusted-external
    expected_signal: "exit_code=0 and 1 scenario passed"
    evidence_required: true
    risk_tags: []
    blocking: true
```

Every in-scope AC must map to at least one check or artifact review. A check may
cover multiple ACs when evidence explicitly maps the relationship.
`manual-observation` requires actor, steps, observed result, and artifact; "looked
good" is not valid evidence.

## Verification evidence v1

Each piece of fresh evidence is captured in a structured record.

```yaml
schema: verification-evidence/v1
evidence_id: EVD-VER-001
verification_run_id: VER-CHG-001-01
candidate_lock: "sha256:..."
check_id: CHK-AC-001
claim_refs: [AC-001]
command: "<exact command>"
command_source: docs/WORKFLOW.md
working_directory: "<repo-relative path>"
environment:
  runner: local-isolated | ci | trusted-external
  os: ""
  runtime_versions: {}
  dependency_lock_hash: ""
started_at: ""
duration_ms: 0
exit_code: 0
result: pass | fail | blocked
summary: ""
output_ref: ""
artifact_refs: []
attempt: 1
redactions: []
```

Evidence policy:

- Exact command, cwd, exit code, timestamp, and candidate lock are required.
- Output summary must not hide failure counts.
- Large raw output is stored separately; the record links and excerpts relevant
  portions.
- Secrets, tokens, and PII must be redacted; never store credentials.
- Screenshots and videos must include scenario, steps, and expected result.
- Coverage is a supporting metric, not a replacement for behavior proof.
- Static code inspection is evidence for structure and coherence, not a
  replacement for runtime tests when the AC describes runtime behavior.

## Verification finding v1

Findings are structured, actionable, and severity-classified.

```yaml
schema: verification-finding/v1
finding_id: VF-001
verification_run_id: VER-CHG-001-01
candidate_lock: "sha256:..."
category: acceptance | correctness | security | reliability | performance | coherence | release | evidence
severity: blocker | major | minor | observation
claim_refs: [AC-001]
location_refs: [src/example.ts:42]
evidence_refs: [artifacts/evidence/CHG-001/verify/CHK-AC-001.json]
expected: ""
observed: ""
impact: ""
reproduction: []
recommended_fix_boundary: []
disposition: open | non-blocking-by-policy | accepted-existing-risk | false-positive
disposition_reason: null
```

Severity definitions:

- `blocker`: failed required check or AC; security boundary violation; data loss;
  incompatible public contract; candidate or evidence integrity failure.
- `major`: material defect or risk in approved scope; needs fix before H3 accept.
- `minor`: bounded maintainability, test, or documentation gap that does not
  violate approved behavior per policy.
- `observation`: information outside scope or future improvement suggestion.

A `major` defaults to blocking until repository policy or human disposition says
otherwise. `minor` does not block but must be recorded. `false-positive` requires
technical reasoning and evidence, not just "reviewer was wrong."

## Verification handoff v2

```yaml
schema: verification-handoff/v2
verification_run_id: VER-CHG-001-01
change_id: CHG-001
implementation_run_id: null
implementation_handoff_ref: artifacts/handoffs/CHG-001/implementation-handoff.json
approval_ref: HITL-H1-001
discovery_handoff_ref: artifacts/handoffs/CHG-001/discovery-handoff.json
candidate_lock:
  type: git-commit
  value: "<full-sha>"
  base_revision: "<full-sha>"
release_required: false
release_profile: none
status: ready-for-H3 | failed | blocked
reviewer:
  agent: reviewer
  skills: [sk-quality-check]
  independence: fresh-context
dimensions:
  completeness: pass | fail | blocked
  correctness: pass | fail | blocked
  coherence: pass | fail | blocked
acceptance_results:
  - acceptance_ref: AC-001
    verdict: satisfied | failed | blocked | not-applicable
    evidence_refs: []
    finding_refs: []
check_results:
  - check_id: CHK-AC-001
    required: true
    result: pass | fail | blocked | skipped
    evidence_refs: []
    reason: null
findings: []
observations: []
release_result: not-requested | pass | fail | blocked
skipped_checks: []
limitations: []
pre_state_hash: ""
post_state_hash: ""
recommended_h3_actions: [accept, return-for-fix]
next_gate: H3
```

### Validation invariants

- `ready-for-H3` requires `pre_state_hash` equals `post_state_hash`.
- `ready-for-H3` requires every required check result is `pass`.
- Required check `skipped`, `blocked`, or missing evidence prevents
  `ready-for-H3`.
- Every in-scope AC must appear exactly once in `acceptance_results`.
- AC `satisfied` must have at least one `evidence_ref`.
- AC `not-applicable` must have an approved reason or reference.
- Open `blocker` or `major` finding prevents `ready-for-H3`.
- `release_required=true` requires `sk-release-check` in skill list and
  `release_result=pass`.
- `release_required=false` requires `release_result=not-requested`.
- Null, interrupted, or malformed reviewer result becomes `blocked`.
- Candidate lock must match the implementation handoff and every evidence record.
- `next_gate` is always H3; the workflow does not emit release side effects.
- `implementation_run_id` is optional (null when consuming
  `implementation-handoff/v1`).

### Reviewer status values

- `pass`: all ACs satisfied, all required checks pass, no blocking findings.
- `pass-with-observations`: all ACs satisfied, but observations recorded; each
  observation must have disposition `non-blocking-by-policy` or
  `accepted-existing-risk`.
- `fail`: at least one AC failed or one blocking finding is open.
- `blocked`: evidence or authority is insufficient to complete review.

### Fix loop

When verification fails:

1. Select blocking finding IDs from the findings list.
2. Create a fix contract for `wf-implement mode=fix` with only the allowed
   findings, paths, AC refs, and required tests.
3. If the fix requires product, design, or public-contract changes beyond H1
   scope, route back to `wf-discover` instead.
4. The fix produces a new candidate ref.
5. Run a full new verification run; do not verify only the delta and carry
   forward old verdicts.
6. Default maximum two fix rounds before escalating to human diagnosis.

