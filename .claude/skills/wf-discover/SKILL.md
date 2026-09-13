---
name: wf-discover
description: Use when a new app, feature, change request, or materially ambiguous behavior needs repository-grounded definition before implementation.
---

# Discover

Produce an evidence-backed discovery result and stop before implementation.

## Inputs

Resolve the request sources, repository mode, base revision, timebox,
constraints, and requested output. Read applicable `AGENTS.md` and
`docs/WORKFLOW.md` first.

## Workflow

1. Capture the repository boundary without mutation. Record the Git root, base
   revision, and dirty status.
2. Resolve intake from the user request and repository state: identify
   `request_sources` (file paths or inline content), `repository_mode`
   (greenfield or brownfield), constraints, and `requested_output`
   (recommendation or buildable-change). Create a local `change_id` if none
   exists.
3. Delegate one task to `architect`; require `$sk-solution-design`. Include in
   the delegation: `change_id`, `request_sources`, `repository_mode`,
   `base_revision`, constraints, timebox, and `requested_output`.
4. When the agent returns `needs-input`, ask the user exactly the blocking
   question supplied, record the answer, and resume the same `change_id`.
5. Treat null, interrupted, malformed, or authority-violating results as
   `blocked`; never repair them into a pass.
6. After architect returns, run `scripts/validate-discovery-handoff.py` against
   the result. Treat validation failure as `blocked`.
7. Compare the working tree diff against allowed paths; reject mutations outside
   `docs/` and `artifacts/handoffs/`.
8. Persist approved proposal artifacts only in repository Harness locations.
9. Emit `discovery-handoff/v2`. For a buildable change, present the final package and stop at H1.

Spike output is a recommendation, not reusable implementation. Bounded and
architectural changes require H1 before implementation.

Do not invoke implementation skills, edit application code, approve decisions,
or continue into `$wf-implement` in the same turn.

Read `../../../docs/workflows/handoff-contracts.md` for the required discovery
handoff fields and gate semantics.
