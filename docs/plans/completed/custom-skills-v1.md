# Execution Plan: Agentic Workflow Harness

Date: 2026-09-10
Completed: 2026-09-13

## Status

Completed

## Outcome

Implement and validate the three workflows, four agents, and six renamed project
skills defined by `harness-agentic-development-workflows-hitl-playbook-vi.md`,
without changing the four installed Harness core skills or inventing missing
product policy.

## Context

- `harness-agentic-development-workflows-hitl-playbook-vi.md` defines the
  accepted names, role boundaries, routing, handoffs, and H1-H3 gates.
- `AGENTS.md` and `docs/WORKFLOW.md` define repository authority, planning, and
  validation boundaries.
- `.agents/skills/` contains the installed Harness core skills, which remain
  unchanged.

## Scope

In scope:

- Canonical project skills: `sk-solution-design`, `sk-backend-engineering`,
  `sk-ai-engineering`, `sk-test-engineering`, `sk-quality-check`, and
  `sk-release-check`.
- Codex project agents `architect`, `backend-dev`, `ai-dev`, and `reviewer`, and
  the three `wf-*` orchestration skills.
- Mechanical validation for naming, generic capability boundaries, agent tool
  and skill assignment, workflow routing, HITL gates, and null results.
- Fresh-session discovery and behavioral validation with Codex.

Out of scope:

- Changes to installed Harness core skills.
- Product implementation or a real provider integration.
- New product rules, provider choices, retry limits, state models, rubrics, or
  release criteria not accepted by a repository authority.

## Approach

Perform the rename atomically, keep `.agents/skills/` canonical, define Codex
custom agents under `.codex/agents/`, and encode the playbook checklist in one
native validator. Implement the three workflows as Codex skills. Keep common
capability entrypoints generic and route repository-specific procedures through
references.

## Risks And Recovery

- Generic reference material could be mistaken for product authority. Each
  reference must point back to accepted repository contracts and stop when they
  are absent.
- Automatic routing could overlap adjacent skills. Preserve the positive and
  near-miss boundaries from the specification and test them in fresh sessions.
- Recovery is restoration of the renamed project-skill directories and removal
  of the new `.codex/` agent definitions and `wf-*` skills; Harness core skill
  directories are not touched.

## Progress

- [x] Read the skill specification, Repository Harness workflow, and skill-creator
  instructions.
- [x] Create the four Iteration 1 skill entrypoints and UI metadata.
- [x] Add only the Iteration 1 references required by entrypoint routing.
- [x] Run static validation for every Iteration 1 skill.
- [x] Run discovery and representative explicit routing and gate evaluations in
  fresh Codex sessions. Workflow skills are intentionally explicit-only.
- [x] Rename all six project skills in one change and update their metadata.
- [x] Generalize the shared backend, AI, and quality capability entrypoints.
- [x] Create the four role-bounded Codex custom agents.
- [x] Create Codex skills `wf-discover`, `wf-implement`, and `wf-verify` with
  H1-H3 handling.
- [x] Remove the incorrect Claude runtime projection and add Codex-native harness
  validation.
- [x] Run fresh-session workflow and routing evaluations with Codex 0.154.0.

## Decisions

- 2026-09-10: Interpret "start implement" as Iteration 1 because the source
  specification explicitly stages the rollout and defers provider/release work.
- 2026-09-10: Keep automatic invocation enabled because the specification routes
  skills by intent and does not request explicit-only invocation.
- 2026-09-10: Omit optional scripts until a machine-readable state contract or a
  concrete artifact format makes deterministic automation useful.
- 2026-09-12: Adopt the playbook rename table as repository authority. Keep
  project-specific composition, speech/timeline, and artifact procedures behind
  the generic `sk-ai-engineering` project-extension reference.
- 2026-09-12: Target Codex rather than Claude. Use `.agents/skills/` directly,
  `.codex/agents/*.toml` for custom roles, and no `.claude/` projection.
- 2026-09-12: Implement each HITL stage as a separate Codex workflow skill so a
  human decision can occur naturally between turns.
- 2026-09-13: Keep fixture-provider implementation outside this harness plan;
  it is a separate product slice requiring its own approved requirements and
  evidence.
- 2026-09-13: Upgrade the global Codex CLI from 0.133.0 to npm latest 0.154.0.
  The current `[agents]` configuration loads under strict configuration.
- 2026-09-13: Namespace all six repository-owned capability skills with `sk-`;
  keep the three orchestration skills under the separate `wf-` prefix.

## Validation

- Focused proof: run the skill-creator `quick_validate.py` against each renamed
  canonical skill and run `scripts/validate-agent-harness.ps1`.
- Negative proof: introduce one controlled reviewer write permission, confirm
  the validator rejects it, then restore the valid definition.
- Integration or end-to-end proof: run the playbook's workflow, explicit
  invocation, and routing cases in fresh Codex sessions.
- Repository-required checks: run `skills-ref validate` and
  `skills-ref read-properties` when that command is available. The command was
  not installed or on `PATH` on 2026-09-12; bundled `quick_validate.py` and a
  local specification, cross-reference, and metadata check passed for all nine
  project skills.

## Result

The Codex-native harness is complete for this scope:

- all nine project skills passed the skill-creator validator;
- the repository harness validator passed for six capability skills, three
  workflow skills, four custom agents, routing, HITL gates, and null safeguards;
- TOML and YAML parsing passed;
- controlled negative proof rejected a write-enabled reviewer and passed after
  restoring `sandbox_mode = "read-only"`;
- a fresh strict-config Codex session discovered all workflow skills and custom
  agents;
- explicit `$wf-discover` delegated exactly once to `architect`, returned a
  `discovery-handoff/v1`, and stopped at H1;
- fresh `$wf-implement` and `$wf-verify` checks stopped as `blocked` when their
  required approval or candidate inputs were absent, without delegation or
  writes; and
- `codex --version` and the npm registry both reported 0.154.0.
- after the namespace follow-up, all six `sk-*` capability names were discovered
  in a fresh read-only Codex session and all six unprefixed entrypoints were
  absent.

`codex doctor --summary` loaded the configuration but returned a nonzero status
because the noninteractive test shell exposed `TERM=dumb`; this is an
environment warning, not a repository configuration failure. Full product
implementation and real-provider validation remain separate work.
