# State And Recovery

Use this reference for write paths, state transitions, transactions, background
execution, messaging, leases, retries, cancellation, and reconciliation.

## Required Authority

Locate accepted state ownership, allowed transitions, validation, delivery and
acknowledgement semantics, retry and backoff limits, idempotency identity,
terminal failure behavior, and recovery ownership. Defaults and current code do
not decide missing policy.

## Trace Before Editing

For each write or asynchronous boundary, identify:

- valid inputs and allowed source and destination states;
- the transaction owner and commit or acknowledgement point;
- what is durable, what may repeat, and what may be observed concurrently;
- atomicity, uniqueness, idempotency, and coordination controls;
- timeout and cancellation behavior;
- duplicate delivery, retry exhaustion, stale work, restart, and reconciliation
  paths; and
- diagnostic events and fields that exclude secrets and sensitive payloads.

For asynchronous work, trace the full durable path from the originating commit
through publication, claim, side effect, result persistence, acknowledgement,
and recovery.

## Proof

Exercise accepted transitions and reject forbidden ones. Demonstrate applicable
rollback, duplicate, concurrent, timeout, cancellation, retry-exhaustion,
restart, and stale-claim behavior with controllable fakes. Verify observability
is sufficient to distinguish inherited, transient, terminal, and recovered
failures without exposing sensitive data.

Stop when any required state, delivery, retry, idempotency, cancellation, or
recovery semantic is unresolved.
