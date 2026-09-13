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
2. Verify approval decision and expiry, change and scope, handoff hash, base
   revision, and approval conditions.
3. Snapshot the current revision, branch or worktree, and pre-existing dirty
   files. Preserve their ownership; never clean or overwrite user changes.
4. Run only repository-owned baseline checks relevant to distinguishing
   inherited failures from introduced failures.
5. Stop without delegation when approval or identity is stale, scope is
   ambiguous, or a requirement, public contract, plan decision, or acceptance
   oracle is missing.

## Execute And Checkpoint

Build the dependency graph, persist `implementation-progress/v2`, and dispatch
only runnable packages. After every returned result or gate transition, validate
the package checkpoint and update the ledger.

Retry a package only when input, diagnosis, context, or strategy changes. The
default maximum is two fix rounds unless repository authority supplies another
finite cap. Never repeat the same prompt or command blindly.

Stop immediately before an H2 action. The approval must match the exact action,
target, limits, rollback, idempotency identity, and expiry. A rejected, expired,
null, or mismatched record yields `blocked`; it does not authorize a mock result
to be represented as a real action.

## Resume

Reload the ledger and revalidate the run ID, H1 approval, handoff hash, base
identity, task result identities, evidence, and dependency graph. Do not
redispatch a `done` task whose diff and evidence still match. Mark an interrupted
`in-progress` task `needs-context` before deciding whether a justified retry is
available, then continue from the first runnable package.

## Integrate And Hand Off

Integrate in dependency order and run the required checks on the whole
candidate. Compare every approved requirement, acceptance criterion, decision,
and plan item with the candidate as `satisfied`, `partial`, `missing`,
`contradicts`, or `unrequested-change`.

Any material result other than `satisfied` prevents readiness. Route plan or
authority defects back to discovery; otherwise append bounded remaining work.
Create either a full commit identity or a content manifest. A dirty tree without
a matching manifest is not immutable.

Emit `implementation-handoff/v2` only after package evidence, final checks,
conformance, candidate identity, and pending H2 status all pass. This is an
implementation checkpoint for independent verification, not H3 acceptance or
release readiness.
