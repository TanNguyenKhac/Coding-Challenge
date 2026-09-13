---
name: sk-backend-engineering
description: Use when an implementation task changes server-side interfaces, state, persistence, asynchronous processing, reliability, or recovery behavior.
---

# Backend Engineering

Implement the smallest approved server-side slice and return traceable behavior,
tests, and evidence without inventing product or reliability policy.

## Mode Routing

- For transport interfaces and error contracts, read `references/api-slice.md`.
- For application workflow state, transitions, checkpoints, or routing, read
  `references/application-workflows.md`.
- For write paths, concurrency, asynchronous work, retries, cancellation, and
  recovery, read `references/state-and-recovery.md`.
- For schemas, migrations, backfills, compatibility, and rollback, read
  `references/data-change.md`.

Read only the references required by the current task.

## Inputs And Invariants

Require an approved contract, observable acceptance criteria, allowed paths,
declared test mode, and repository-owned checks. Established code and tests show
current behavior; they do not decide missing interface, state, retry, or
ownership policy.

Before editing, describe affected state transitions, invariants, callers and
callees, failure modes, and transaction or delivery boundaries. Keep model or
provider integration in `sk-ai-engineering`.

## Procedure

1. Inspect the approved contract and the repository's established implementation
   and test patterns.
2. Select the relevant references and trace the complete affected boundary.
3. Use `$sk-test-engineering` with the package's declared test mode. For a TDD
   task, observe the intended RED failure before minimal implementation.
4. Implement one coherent diff inside allowed paths. Do not perform unrelated
   cleanup or opportunistic refactoring.
5. Exercise applicable validation, atomicity, idempotency, concurrency, retry,
   duplicate delivery, timeout, cancellation, and recovery behavior.
6. Add diagnostic observability needed by the approved behavior without logging
   credentials, secrets, or sensitive payloads.
7. Run focused and repository-required checks, self-review the diff, and capture
   fresh reproducible evidence.

## Stop Conditions

Stop on missing acceptance or failure semantics, unresolved interface or state
ownership, unspecified retry/idempotency behavior, destructive or incompatible
data change without rollout and recovery authority, H2 action, path conflict,
or required work outside the approved package.

## Output Contract

When invoked with `work-package/v2`, return `agent-task-result/v2` with changed
paths, requirement and acceptance trace, declared test-mode evidence, exact
commands and exit codes, migration or recovery implications, self-review,
concerns, and deviations. If implementation would require a contract delta,
report it and stop; do not apply an unapproved delta.
