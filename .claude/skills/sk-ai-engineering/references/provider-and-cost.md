# Provider And Cost

Use this reference for provider ports and adapters, capability checks, failure
translation, live calls, timeouts, retries, rate limits, fallback, caching, and
cost controls.

## Required Authority

Locate the accepted application port, routing decision, typed failure taxonomy,
capability contract, timeout and retry limits, fallback policy, idempotency
identity, cache semantics, privacy rules, and call or cost budget. Provider SDKs
and defaults do not establish application policy.

## Implementation

- Keep provider selection outside application domain logic and SDK types inside
  the adapter.
- Verify every used capability from authoritative documentation or an
  authorized probe.
- Make timeout, bounded retry/backoff, rate-limit response, fallback, and
  idempotency behavior explicit.
- Define cache identity, hit/miss behavior, invalidation, retention, and
  sensitive-data handling from approved policy.
- Keep real calls disabled in deterministic tests. Require an action-scoped H2
  record before any otherwise-unapproved paid or production call.

## Proof And Evidence

Use deterministic fixtures for request mapping, malformed or incomplete
responses, throttling, unavailability, timeout, retry exhaustion, fallback, and
cache behavior. Record relevant provider/model version, limits, cache outcome,
and sanitized provenance. Never persist credentials or raw sensitive payloads.

Stop when capability, error mapping, retry, fallback, cache, privacy, cost, or
live-system authority is unresolved.
