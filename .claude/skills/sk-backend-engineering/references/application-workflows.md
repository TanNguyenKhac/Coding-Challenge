# Application Workflow Procedure

Use this reference for application-owned workflow state, steps, transitions,
checkpoints, resume behavior, and routing, independent of orchestration
technology.

## Required Authority

Locate the accepted workflow input/output schema, transitions, checkpoint
ownership, routing decisions, and failure categories. Provider-specific
capabilities remain outside this skill.

## Trace

Represent each node by its required input state, emitted state, possible failure
category, and durable checkpoint behavior. Identify which transitions may repeat
after resume and which side effects therefore require idempotency.

Keep application workflow state infrastructure-neutral. Pass external requests
through approved interfaces; do not import implementation-specific types into
domain or workflow contracts.

## Implementation Proof

- Test accepted transitions and terminal results.
- Exercise failure at changed node boundaries.
- Resume from the latest approved checkpoint without repeating non-repeatable
  work.
- Prove routing follows accepted application decisions.
- Persist only the approved result or artifact reference.

Stop when workflow ownership, routing, checkpoint durability, resume semantics,
or failure mapping is unresolved.
