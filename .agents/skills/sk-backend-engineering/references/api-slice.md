# API Slice Procedure

Use this reference for transport adapters, request and response schemas, status
codes, and externally visible error mapping, independent of framework.

## Required Authority

Locate the accepted requirement, interface contract, and relevant decision
record before editing.
Treat existing handlers and tests as current-behavior evidence, not authority for
an unresolved external contract.

## Trace

Map the full observable path:

```text
request parsing -> validation -> application command/query -> transaction or
enqueue boundary -> response mapping -> documented error response
```

Record authentication and authorization boundaries when they are in scope.
Confirm which layer owns each validation rule and avoid duplicating domain rules
inside transport schemas.

## Implementation Proof

- Exercise accepted success status and response schema.
- Exercise malformed input and every changed accepted error mapping.
- Prove that rejected requests do not perform forbidden writes or enqueue work.
- For idempotent endpoints, test the accepted identity key and replay result.
- Keep infrastructure types and internal execution payloads out of public
  interfaces.

Stop when a status code, field, error body, authorization rule, or idempotency
contract is materially ambiguous.
