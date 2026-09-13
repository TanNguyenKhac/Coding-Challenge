---
name: sk-quality-check
description: Use when independently verifying an immutable candidate against approved requirements, acceptance criteria, repository invariants, tests, and risk-based correctness checks.
---

# Quality Check

Produce evidence-backed per-AC verdicts for an immutable candidate without
modifying it.

## Authority

- Approved requirements, acceptance criteria, and decisions from the discovery
  handoff and verification contract.
- Repository-defined or task-supplied evaluation oracles and rubrics.
- Repository policy for invariants, tests, and evidence standards.

Do not invent expected behavior, infer missing oracles, or elevate current code
patterns to product policy.

## Mode Routing

- For executing approved commands and capturing evidence, read
  `references/command-verification.md`.
- For evaluating outputs against a supplied oracle or rubric, read
  `references/output-evaluation.md`.
- For the evidence record format, read `references/evidence-schema.md`.
- For the two-pass review procedure and dimensions, read
  `references/review-dimensions.md`.
- For risk-triggered probes, read `references/risk-probes.md`.
- For test quality, flake diagnosis, and repeatability policy, read
  `references/test-and-flake-review.md`.

Read only the references relevant to the requested evaluation.

## Procedure

1. Validate candidate identity and authority chain. Confirm candidate lock
   matches the implementation handoff.
2. Build requirement/AC/decision/work-package inventory from approved contracts.
   Do not infer missing oracles.
3. Inspect diff plus affected dependents, not only changed files. Check changed
   paths against approved scope.
4. **Pass A — Completeness and deterministic evidence:**
   a. Map every in-scope AC to checks, evidence, or artifact review.
   b. Rerun fresh required checks on the exact candidate.
   c. Read full relevant output, exit codes, and failure counts.
   d. Verify evidence carries candidate identity.
   e. Detect missing tasks, unrequested changes, and undocumented deviations.
   f. Assign per-AC verdicts: `satisfied`, `failed`, `blocked`, or
      `not-applicable`.
5. **Pass B — Adversarial correctness and coherence:**
   a. Scout blast radius: callers/consumers of changed interfaces, state
      transitions, shared mutable state, async ordering, retry/timeout,
      validation boundaries, error propagation, and observability.
   b. Verify completeness: every approved REQ/AC/task has implementation and
      proof; no unrequested change is hidden.
   c. Verify correctness: positive, negative, boundary, and recovery behavior
      matches the oracle.
   d. Verify coherence: implementation follows approved design, repository
      patterns, dependency direction, and public contracts.
6. Check negative/boundary/recovery scenarios according to risk tags in the
   verification plan.
7. Inspect test quality: observable assertions, fake fidelity, false-positive
   risk, regression sensitivity.
8. Distinguish introduced, inherited, and environment failures.
9. Emit actionable findings with expected/observed/impact/reproduction and
   recommended fix boundary.
10. Snapshot candidate state after review; confirm pre/post match.

## Anti-patterns

Do not accept these as proof:

- `tests pass` => requirements met;
- `task marked done` => implementation complete;
- `grep found keyword` => requirement exists;
- `coverage high` => tests are meaningful;
- `screenshot looks right` => contract met;
- `reviewer confidence` => evidence;
- `rerun passed once` => flake resolved;
- style nit elevated to release blocker without policy.

## Stop Conditions

Report `blocked` when:

- required artifacts, reference packs, or rubrics are missing;
- the environment or dependency required for execution is unavailable;
- required credentials are unavailable;
- candidate identity cannot be confirmed or has drifted;
- two rubric interpretations yield materially different results.

## Output Contract

Return per-AC verdicts, evidence refs, actionable findings with severity and
disposition, limitations, and pre/post candidate state identity. Keep failed,
skipped, and blocked checks visible. Do not store chain-of-thought; store
decisions, actions, observations, and proof.
