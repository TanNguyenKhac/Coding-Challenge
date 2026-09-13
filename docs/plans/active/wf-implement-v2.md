# Execution Plan: WF Implement v2

Date: 2026-09-13

## Status

Active

## Outcome

Upgrade `wf-implement`, its two implementation agents, and its three capability
skills to the approved v2 contract so implementation can be bounded, resumed,
evidence-checked, and handed to `wf-verify` as a fixed candidate.

## Context

- `wf-implement-v2-optimization-vi.md` is the accepted task authority for the
  v2 modes, contracts, gates, routing, evidence, and validation rules.
- `AGENTS.md` and `docs/WORKFLOW.md` define repository authority, durable-plan,
  delegation, and completion boundaries.
- `docs/workflows/handoff-contracts.md` owns cross-workflow schemas.
- `scripts/validate-agent-harness.ps1` is the native static validation owner.

## Scope

In scope:

- `work-package/v2`, `agent-task-result/v2`, `implementation-progress/v2`, H2,
  candidate, and `implementation-handoff/v2` contracts.
- The existing `wf-implement`, `backend-dev`, and `ai-dev` definitions.
- The existing backend, AI, and test engineering skills and their focused
  references.
- Static positive and controlled negative proof for the accepted harness
  invariants.

Out of scope:

- New workflows, agents, or capability skills.
- Changes to `wf-discover`, the independent reviewer role, or H3 semantics.
- Product implementation, live provider calls, CI configuration, hooks, and
  branch-protection changes.

## Approach

Define schemas once in the handoff contract, keep the workflow entrypoint short,
move conditional mechanics into references, tighten each agent to one work
package, then make the capability skills consume the declared test and evidence
contract. Extend the existing validator instead of adding another framework.

## Risks And Recovery

- Duplicate schema text could drift. Keep full schemas only in
  `docs/workflows/handoff-contracts.md`; skill references link to it.
- Existing v1 handoffs could become unreadable. Retain v1 as a legacy input
  during migration while requiring new WF2 output to use v2.
- A broad validator could encode preferences not in authority. Restrict new
  checks to rules stated in `wf-implement-v2-optimization-vi.md` and include the
  authority and repair action in diagnostics.
- Recovery is reverting the files listed in this plan; no production or
  external state is touched.

## Progress

- [x] Read repository workflow, v2 design, existing contracts, skills, agents,
  references, and validator.
- [ ] Add canonical v2 contracts and artifact guidance.
- [ ] Update `wf-implement` and its progressive-disclosure references.
- [ ] Tighten the two agent contracts and three capability skills.
- [ ] Extend and run native validation, skill validation, parsing, and controlled
  negative proof.
- [ ] Record the verified result and move this plan to `docs/plans/completed/`.

## Decisions

- 2026-09-13: Treat the user-supplied v2 design as accepted authority for this
  repository-local workflow optimization.
- 2026-09-13: Retain v1 handoff documentation for legacy readers because no
  active v1 run artifact exists; all new WF2 writers emit v2.
- 2026-09-13: Use the existing PowerShell harness validator as the mechanical
  enforcement owner; do not add CI, hooks, or external policy.

## Validation

- Focused proof: run the bundled skill validator for all four changed skills;
  parse changed TOML/YAML; run `scripts/validate-agent-harness.ps1`.
- Negative proof: temporarily introduce one prohibited WF2 reviewer reference,
  confirm the native validator rejects it for the intended v2 rule, then restore
  and rerun the positive case.
- Integration proof: run bounded fresh-session scenarios where practical and
  report any IMP-01..IMP-22 cases not evaluated.
- Repository-required checks: the harness validator and any discoverable
  repository-native metadata checks.

## Result

Pending implementation and validation.
