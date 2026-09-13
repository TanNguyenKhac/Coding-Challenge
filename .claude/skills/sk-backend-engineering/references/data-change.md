# Data Change

Use this reference for schema changes, migrations, backfills, index or constraint
changes, and data-lifecycle compatibility.

## Required Authority

Locate the approved data owner, compatibility window, rollout order, backfill
semantics, validation query or oracle, and rollback or roll-forward strategy.
A current schema or migration tool does not authorize a destructive change.

## Procedure

Separate and prove the applicable phases:

1. introduce a compatible schema or representation;
2. deploy readers and writers that tolerate the transition window;
3. backfill with explicit batching, restart, idempotency, and failure behavior;
4. validate completeness and correctness using the approved oracle; and
5. remove legacy shape only after the accepted cutover condition.

Record lock, transaction, availability, retention, and rollback implications.
Use the repository's migration tooling and exercise upgrade plus the approved
recovery path.

Stop before incompatible or destructive execution when backup, rollout,
backfill, cutover, or recovery behavior is absent or when H2 is required.
