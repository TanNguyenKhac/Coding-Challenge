# Workflow artifacts

Durable workflow outputs use these repository-owned locations when persistence
is requested:

- `handoffs/` for discovery, approval, implementation, and verification
  documents. New implementation writers use `implementation-handoff/v2`;
- `evidence/` for `implementation-progress/v2`, task and command results,
  candidate manifests, evaluation evidence, checksums, and provenance.

Ephemeral conversation state remains in the workflow runtime. Persist only the
approved recovery and proof artifacts required by a durable run, and never
store them under `.harness-core/`. Never persist credentials, raw secrets, or
chain-of-thought.
