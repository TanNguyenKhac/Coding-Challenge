# Execution And Resume

Read the canonical approval, progress, candidate, and handoff schemas in
[`docs/workflows/handoff-contracts.md`](../../../../docs/workflows/handoff-contracts.md).

## Select The Mode

- `apply`: require `change_id`, `approval_ref`, and
  `discovery_handoff_ref` for a new approved change.
- `resume`: require `change_id` and `implementation_run_id`; reload durable
  state rather than reconstructing it from conversation history.
- `fix`: require `change_id`, a fixed `candidate_ref`, bounded `finding_refs`,
  and an H1 approval that still covers the work.

Default to `apply` only when the supplied inputs describe a new run
unambiguously.

## Read-Only Preflight

Before mutation:

1. Resolve one change and load its discovery handoff, approval, plan, required
   checks, allowed and protected paths, and H2 policy.
2. Verify approval decision and expiry, change and scope, handoff hash, and
   approval conditions. Apply the mode-specific identity rule:
   - `apply`: current pre-mutation identity equals the H1 base revision;
   - `resume`: current state matches the ledger and completed result identities
     rooted at that base; and
   - `fix`: current state matches the supplied candidate ref while H1 scope and
     conditions still cover the findings.
3. Persist a digest-bound `implementation-preflight/v1` with current revision,
   branch or worktree, starting content identity, and pre-existing dirty paths
   and ownership. Never clean or overwrite user changes; block a package that
   overlaps user-owned dirt until ownership and scope are resolved.
4. Run only repository-owned baseline checks relevant to distinguishing
   inherited failures from introduced failures.
5. Stop without delegation when approval or identity is stale, scope is
   ambiguous, or a requirement, public contract, plan decision, or acceptance
   oracle is missing.

## Execute And Checkpoint

Build the dependency graph, persist `implementation-progress/v2`, and dispatch
only runnable packages. After every returned result or gate transition, validate
the package checkpoint and update the ledger.

For an H2 action, journal `planned`/`waiting-human`, the exact approval, the
`in-progress` transition immediately before execution, and the observed terminal
result. If completion cannot be established after interruption, record
`uncertain` and reconcile by idempotency identity and target state before any
retry.

Retry a package only when input, diagnosis, context, or strategy changes. The
default maximum is two fix rounds unless repository authority supplies another
finite cap. Never repeat the same prompt or command blindly.

Stop immediately before an H2 action. The approval must match the exact action,
target, limits, rollback, idempotency identity, and expiry. A rejected, expired,
null, or mismatched record yields `blocked`; it does not authorize a mock result
to be represented as a real action.

## Resume

Reload the ledger and revalidate the run ID, H1 approval, handoff hash, approved
base root, current ledger identity, completed task result identities, evidence,
dependency graph, and external-action journal. Do not redispatch a `done` task
whose diff and evidence still match. Mark an interrupted `in-progress` task
`needs-context` before deciding whether a justified retry is available. An
external action left `in-progress` becomes `uncertain` and cannot be retried
until idempotency and target-state reconciliation prove it safe. Continue from
the first runnable package only after these checks.

## Integrate And Hand Off

Integrate in dependency order and run the required checks on the whole
candidate. Compare every approved requirement, acceptance criterion, decision,
and plan item with the candidate as `satisfied`, `partial`, `missing`,
`contradicts`, or `unrequested-change`.

Any material result other than `satisfied` prevents readiness. Route plan or
authority defects back to discovery; otherwise append bounded remaining work.
Create either a full commit identity or a content manifest. A dirty tree without
a matching `candidate-manifest/v1` whose own digest, preflight binding, complete
added/changed/renamed/deleted path set, and repository content identities
revalidate is not immutable.

Emit `implementation-handoff/v2` only after package evidence, final checks,
recorded conformance entries, explicit concern dispositions, candidate identity,
and pending or uncertain H2 status all pass. This is an implementation
checkpoint for independent verification, not H3 acceptance or release readiness.
