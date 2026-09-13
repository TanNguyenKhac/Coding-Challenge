# Discovery Modes

This reference defines the criteria, outputs, and rules for classifying
discovery depth. The governing skill (`sk-solution-design`) selects exactly one
mode per change after an initial repository inspection.

## Mode selection

### `spike`

Use when the requested output is a feasibility answer or recommendation, not
retained implementation code.

Examples:

- Can the existing framework support streaming responses?
- Is provider X compatible with our persistence model?
- What is the cheapest experiment to validate an assumption?

Indicators:

- The user asked a question, not requested a build.
- No implementation artifact is expected to survive the investigation.
- The answer may lead to a follow-up bounded or architectural change.

Required output:

- question being investigated;
- method and probe boundary;
- evidence gathered;
- finding;
- recommendation;
- follow-up change suggestion if the user decides to build.

Spike does not produce an implementation handoff. Experimental code, if any,
must be explicitly permitted and marked throwaway.

### `bounded`

Use when all of the following are true:

- The flow being changed already exists in the repository.
- Scope is small with one primary owner.
- No new public contract, data ownership change, or security boundary change.
- The change can be completed and verified in one short iteration.

Examples:

- Add a validation rule to an existing endpoint.
- Fix a state transition bug in an existing job flow.
- Add a field to an existing response model.

Required output:

- sourced requirements;
- observable acceptance criteria;
- affected files and surfaces;
- short design;
- required tests and checks;
- H1 package.

Bounded mode does not require a durable ADR or multi-step implementation plan.

### `architectural`

Use when at least one of the following is true:

- Greenfield application or new subsystem.
- Multiple components or agents involved.
- New or changed public interface.
- New persistence or state ownership.
- Security or compliance boundary change.
- Migration or new external provider integration.
- Multi-session change.
- Multiple viable approaches with significant tradeoffs.

Required output:

- sourced requirements and acceptance criteria;
- impact map (interfaces, data, dependencies, tests);
- two or three solution options with comparison;
- recommendation with rationale;
- architecture and design;
- proposed decisions;
- durable implementation plan under `docs/plans/active/`;
- verification contract;
- risks and unknowns;
- H1 package.

## Rules

### One-way escalation

Mode may only be upgraded during a run (bounded → architectural) when hidden
complexity is discovered. Mode must not be downgraded mid-run to skip required
ceremony.

### Greenfield and brownfield

Greenfield repositories almost always require `architectural` mode because
there is no existing flow to constrain scope.

Brownfield repositories default to `bounded` unless the change introduces one
of the architectural indicators listed above.

### Decomposition

When a request spans multiple independent subsystems:

1. Describe each subsystem.
2. Identify dependencies and ordering constraints.
3. Propose each subsystem as a separately deliverable and verifiable change.
4. Select the first change for discovery.
5. Do not create a single mega-plan covering the entire platform.

### Timebox awareness

When a timebox is specified:

- `spike`: always feasible within any reasonable timebox.
- `bounded`: feasible within short timeboxes (under 2 hours).
- `architectural`: full ceremony (options + design + plan + verification
  contract) requires adequate time. When timebox is tight, scope aggressively
  and consider whether the change can be reframed as bounded.

Do not skip required outputs to fit a timebox. Instead, reduce scope until the
required outputs for the selected mode are achievable within the constraint.
