---
name: sk-quality-check
description: Execute approved verification commands and evaluate outputs against repository-defined acceptance criteria or supplied rubrics. This skill is read-only and reports passed, failed, blocked, or not-evaluated with evidence; it must not repair implementation or change acceptance criteria.
---

# Quality Check

## Outcome

Produce a read-only, evidence-backed pass, fail or blocked result for the
requested implementation or generated artifacts.

## Mode Routing

- For tests, builds, lint and runtime checks, read
  `references/command-verification.md`.
- For evaluating outputs against a supplied oracle or rubric, read
  `references/output-evaluation.md`.
- For the result format, read `references/evidence-schema.md`.

Read only the references relevant to the requested evaluation.

## Authority

- Required validation commands
- Approved testcases and acceptance criteria
- Repository-defined or task-supplied evaluation oracle and rubric
- Artifact manifest and repository revision

## Read-Only Boundary

Do not modify source, tests, requirements, decisions or configuration. A failure
opens a separate bounded fix task owned by an implementation agent.

## Procedure

1. Record repository revision, environment and requested evaluation scope.
2. Confirm required commands, rubrics, testcases and artifacts are available.
3. Execute commands without changing the implementation.
4. Record commands, exit codes and relevant observable output.
5. Evaluate the complete required sample set against the supplied rubric.
6. Classify each scope as `passed`, `failed`, `blocked` or `not-evaluated`.
7. Report findings, evidence locations and limitations without cherry-picking.

## Stop Conditions

Report `blocked` when:

- required artifacts, reference packs or rubrics are missing;
- the environment or dependency required for execution is unavailable;
- required credentials are unavailable;
- the artifact set is incomplete or not representative;
- two rubric interpretations yield materially different results.

## Output Contract

- Repository revision and environment
- Requirement and testcase scope
- Commands and exit codes
- Artifact identifiers and checksums
- Technical and rubric-based results
- Evidence-backed findings
- Limitations and recommended bounded fix tasks

Do not store chain-of-thought. Store decisions, actions, observations and proof.

## Validation

- Completion claims match exit codes and artifacts.
- Failed and skipped checks remain visible.
- Findings identify the affected requirement, testcase or artifact.
- Required samples are not omitted.
- Repository status after evaluation matches the initial read-only boundary.
