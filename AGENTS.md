# Agent Instructions

<!-- HARNESS:BEGIN -->
## Harness

Start with the requested outcome and use the repository as the system of record.
Read `docs/WORKFLOW.md` and only relevant product, design, plan, code, and
validation material.

- Answers, explanations, reviews, diagnoses, plans, and status reports are
  read-only. Inspect only what is needed; change nothing.
- For a bounded change, inspect affected behavior and proof, implement, and
  validate. No control-plane operation is required.
- Use one `docs/plans/active/` file when work spans sessions, coordinates
  contributors, has dependencies, or needs recovery. Move it to
  `docs/plans/completed/` only after validation.
- Before editing, identify repository authority for each new externally
  observable policy. If materially different choices remain open, stop before
  edits; configurable defaults are not authority.
- For architecture, reliability, security, or quality invariant work, read
  `docs/patterns/encoding-invariants.md` and enforce only accepted rules.
- Report reusable agent friction. Change guidance, tools, runbooks, or validation
  for that purpose only when explicitly asked to use `$improve-harness`.
- Also pause when product intent remains ambiguous, recovery is difficult,
  validation is weakened, or authority is insufficient.
- Claim completion only with executable or observable evidence. Report outcome,
  changes, validation, and unresolved risks.

Harness has no task database or orchestration lifecycle. Use repository plans
and behavior-level proof; do not create parallel control-plane state.
<!-- HARNESS:END -->

## Project Context

- `docs/product/overview.md`: product requirements, constraints, and evaluation
  criteria for the Chemistry Video Request Service.
- `docs/Agentic_Backend_Challenge_AI_Chemistry_Video_Request_Service.md`: full
  original specification from the challenge provider.

## Codex agentic workflows

Use `.agents/skills/` as the canonical source for both reusable capability
skills and the `wf-discover`, `wf-implement`, and `wf-verify` orchestration
skills. Project custom agent profiles live in `.codex/agents/`; do not create or
maintain a Claude projection.

- `$wf-discover` delegates only to `architect`, returns a
  `discovery-handoff/v2`, and stops for H1.
- `$wf-implement` requires an approving H1 decision and delegates bounded
  packages to `backend-dev` and/or `ai-dev`. Stop for H2 before any recorded
  high-risk action.
- `$wf-verify` delegates only to the read-only `reviewer`, runs release checking
  only when requested, and stops for H3.

Delegate when one of these workflow skills requires it. Parallelize only
independent tasks with disjoint mutable paths; use one writer per mutable
surface. Treat missing or failed subagent results as blocked, never as success.
Use `docs/workflows/handoff-contracts.md` for durable handoff fields and gate
semantics. Keep runtime conversation state in Codex; persist only requested
handoffs and evidence in `artifacts/`.
