---
name: wf-implement
description: Use when implementing an approved repository change, resuming an interrupted implementation run, or applying bounded verification fixes after H1.
---

# Implement

Implement only an approved change and produce an evidence-backed immutable
candidate for `wf-verify`.

## Inputs

Require `change_id` and either an H1-backed discovery handoff (`apply`), an
implementation run (`resume`), or bounded verification finding refs (`fix`).

## Procedure

1. Read repository authority and `references/execution-and-resume.md`.
2. Validate approval, handoff hash, base revision, allowed paths, required
   checks, current repository state, and H2 policy before mutation.
3. If a normative requirement, acceptance oracle, public interface, or plan
   decision is missing, stop and route to `wf-discover`.
4. Compile approved work into `work-package/v2` tasks with one mutable-surface
   owner. Read `references/task-contract.md`.
5. Dispatch `backend-dev` for backend packages and require
   `$sk-backend-engineering` plus `$sk-test-engineering`. Dispatch `ai-dev` for
   AI packages and require `$sk-ai-engineering` plus `$sk-test-engineering`.
6. Parallelize only when every predicate in `references/parallel-safety.md`
   passes; otherwise run packages sequentially.
7. Give each invocation exactly one package and only its referenced context.
   Capture its agent identifier and retrieve that same invocation; do not
   duplicate work because a result is delayed.
8. Before accepting a package, inspect its `agent-task-result/v2`, diff, allowed
   paths, acceptance trace, command exit codes, and repository identity. A
   missing, interrupted, failed, malformed, or null result is never success.
9. Stop at H2 immediately before a gated action. Approval must match its action,
   target, limits, rollback, idempotency identity, and expiry.
10. Integrate in dependency order, run repository-required checks, and compare
    the candidate with approved requirements, acceptance criteria, decisions,
    and plan.
11. Persist `implementation-progress/v2` after every state transition. On
    resume, do not repeat completed work whose evidence and diff still match.
12. Emit `implementation-handoff/v2`. Return `ready-for-verification` only when
    all required work, evidence, conformance, and candidate identity checks pass.

## Stop Conditions

Stop on stale approval or revision, scope expansion, plan defect, unresolved
shared contract, H2 denial or expiry, path conflict, exhausted retry budget,
malformed agent result, or required-check failure.

Never call `reviewer`, self-approve H1/H2/H3, mutate protected scope, or claim
release readiness.
