---
name: sk-solution-design
description: Use when requirements, repository impact, solution choices, or implementation boundaries must be resolved before application code changes.
---

# Solution Design

Turn a request into the smallest evidence-backed decision package that can be
implemented and independently verified.

## Authority

Repository instructions and accepted product/decision documents are normative.
Code, tests, and configuration prove current behavior only. Label every material
claim as Authoritative, Observed, Derived, Decision required, or Unknown.

Use, in order:

1. Explicit user decisions and accepted product requirements.
2. Repository decision records, architecture documents, and active plans.
3. Existing externally observable behavior and executable tests.
4. Implementation patterns only as evidence, never as authority for new policy.

If materially different choices remain open, stop at the decision boundary. Do
not disguise an undecided policy as a configurable default.

## Select depth

After a minimal repository inspection, classify the work as `spike`, `bounded`,
or `architectural`. Read `references/discovery-modes.md` for the criteria and
required outputs per mode. Hidden complexity may upgrade depth; do not downgrade
mid-run to skip ceremony.

## Procedure

1. Capture request sources, repository revision, constraints, success criteria,
   and existing affected behavior.
2. Decompose requests that cannot produce one coherent, verifiable candidate.
   Describe subsystems, dependencies, and delivery order. Choose the first
   independently deliverable change for discovery.
3. Ask one decision-changing question at a time. Record non-blocking assumptions;
   stop on blocking unknowns with status `needs-input`. Only ask when the answer
   could change scope, interface, state, cost, security, artifact, or test
   oracle. Do not ask what the repository already answers.
4. Create sourced requirements and observable acceptance criteria. Every
   requirement must reference its source evidence.
5. Map affected interfaces, data/state, dependencies, tests, risks, and external
   effects.
6. If the request includes domain-specific quality, cost, or reliability
   requirements, identify the applicable evaluation dimensions and include them
   as acceptance criteria and verification contract entries. Do not invent domain
   rubrics; use only those supplied by the request sources or accepted product
   documents.
7. For material choices, compare two or three viable approaches and recommend
   the simplest coherent option. Each option needs: summary, affected
   boundaries, benefits, costs, risks, reversibility, and verification impact.
   Apply YAGNI to scope: exclude what is not needed for the current change.
8. Define component boundaries, contracts, failure behavior, and verification
   oracle. Create a durable plan only when the selected depth requires it; read
   `references/plan-quality.md`.
9. Run the self-review before returning `ready-for-approval`:
   a. Every requirement has source and classification.
   b. Every acceptance criterion is observable.
   c. No contradiction between requirements, options, design, and plan.
   d. Every in-scope requirement has a work package or explicit exclusion reason.
   e. No `TBD`, `TODO`, or vague terms hiding a decision.
   f. Current code behavior is not elevated to product policy.
   g. Shared contracts have an owner.
   h. Required checks have a command or evidence type.
   i. External effects default to deny and route to H2.
   j. Scope is small enough for one candidate to verify.
10. Return `discovery-handoff/v2`; validate it against
    `../../../docs/workflows/handoff-contracts.md`.

## Design sections

Include only relevant sections from: architecture/components,
interfaces/contracts, data/state lifecycle, failure/retry/recovery,
security/external effects, observability, testing/verification,
rollout/migration/rollback. Do not write empty sections or `N/A` placeholders.

## Stop conditions

Return `needs-input` for unresolved product, interface, security, cost, data,
artifact, or acceptance choices. Return `blocked` when repository authority,
revision, or required evidence cannot be established. Never implement, mutate
application surfaces, or accept the proposal.

## Write scope

This skill may create or update approved design, decision, or plan documents
under `docs/` and `artifacts/handoffs/`. It must not edit production
implementation, tests, workflow runtime state, or generated evidence.
