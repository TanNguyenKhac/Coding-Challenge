# Plan Quality

This reference defines when a durable implementation plan is required, the
structure of work packages, and the quality rules that plans must satisfy.

## When is a durable plan required?

Create one plan file under `docs/plans/active/<change-id>-<slug>.md` when:

- The discovery mode is `architectural`.
- Work spans multiple sessions.
- Multiple agents or contributors are involved.
- The change has meaningful dependencies between work packages.
- Recovery from a failed mid-point requires documented state.

A `bounded` change may set `plan.required: false` and include a single work
package directly in the discovery handoff.

A `spike` does not produce an implementation plan.

## Work package structure

Each work package in a plan must include:

- **objective**: what observable result this package produces.
- **requirement_ids**: which requirements this package addresses.
- **candidate_paths**: exact files or surfaces the package may modify.
- **owner_agent**: which agent role owns execution (e.g., `backend-dev`,
  `ai-dev`).
- **interfaces**: what this package consumes from and produces for other
  packages.
- **test_cases**: specific test scenarios with expected behavior.
- **commands**: verification commands to run after implementation.
- **evidence_expected**: what artifacts or outputs prove the package is done.
- **stop_conditions**: when the agent must pause and escalate.
- **dependencies**: which other packages must complete first.
- **order**: execution sequence relative to other packages.

## Owner and shared-surface rules

- Each mutable file or surface has exactly one owner agent per work package.
- When two packages modify the same file, define an explicit interface between
  them and specify execution order.
- Shared contracts (API schemas, database models, configuration) must have a
  single owner package that other packages depend on.

## Interface freeze

When `architectural` mode produces multiple work packages:

- Define shared interfaces in the plan before delegating implementation.
- Implementation agents must not change shared interfaces without returning
  to the discovery workflow.
- If an interface change is discovered during implementation, the agent must
  stop and report a deviation.

## Acceptance-to-task traceability

Every in-scope requirement must map to at least one work package. Every work
package must map to at least one requirement. If a requirement has no work
package, the plan must state the explicit reason (deferred, out of scope, or
covered by another package).

## Verification contract

The plan must include or reference a verification contract specifying:

- **required_checks**: commands or test suites that must pass.
- **acceptance_matrix**: mapping from acceptance criteria to verification
  evidence.
- **required_artifacts**: files or outputs that must exist after implementation.
- **rubric_refs**: references to evaluation rubrics when applicable (from
  request sources or product documents, not invented).
- **repeatability_policy**: how to verify consistent behavior across repeated
  runs when non-determinism is a factor.
- **cost_evidence_policy**: how to verify cost claims when cost is an
  evaluation criterion.
- **release_profile**: `none`, `local-demo`, or a project-specific profile
  documented in `docs/product/`.

## YAGNI and timebox

- Include only the work packages needed for the current approved scope.
- Do not add packages for speculative future features.
- When a timebox constrains implementation, reduce the number of work packages
  by reducing scope — do not reduce the quality of individual packages.
- Each work package should be independently deliverable and verifiable when
  possible.

## Self-review for plans

Before including a plan in a `ready-for-approval` handoff:

1. Every in-scope requirement traces to a work package.
2. Every work package traces to a requirement.
3. No work package has placeholder objectives or vague evidence expectations.
4. Shared surfaces have a single owner per package.
5. Dependencies form a DAG (no cycles).
6. Verification contract covers all acceptance criteria.
7. Stop conditions are explicit for each package.
8. The total scope is achievable within the stated timebox or session boundary.
