---
name: sk-test-engineering
description: Use when deriving, implementing, or running tests and evidence for approved acceptance criteria, contracts, regressions, or implementation changes.
---

# Test Engineering

Produce executable, traceable proof of approved behavior without inventing an
oracle or changing expectations to fit the implementation.

## Test Mode

Select exactly one mode from `references/test-modes.md`: `tdd`,
`characterization`, `contract`, `verification-only`, or `not-applicable`.

## Inputs

Require approved requirement and acceptance refs or a bounded regression
symptom, an observable oracle, allowed paths, known baseline failures, and
repository-owned commands. Existing tests are evidence of current behavior,
not authority to decide missing behavior.

## Procedure

1. Trace every case to requirement/acceptance refs or the supplied regression
   symptom and define its observable result.
2. Declare the test mode and reason before changing implementation.
3. Cover only relevant happy, validation, boundary, failure, transition,
   idempotency, concurrency, and recovery behavior.
4. Prefer a real boundary or faithful deterministic fake. Do not write a test
   that proves only that a mock was called.
5. For TDD, capture a fresh RED run that fails for the intended missing behavior
   before GREEN. For characterization, establish the legacy baseline before
   refactoring. For contract mode, exercise both valid and rejected boundary
   shapes.
6. Rerun focused tests and required repository checks. Separate inherited
   baseline failures from failures introduced by the package.
7. Capture exact commands, timestamps, exit codes, output summaries or artifact
   refs, and ensure evidence contains no credentials, secrets, or sensitive
   payloads.

## Stop Conditions

Stop when expected behavior or the oracle is unapproved, a mock would hide the
boundary under test, required data or environment is unavailable, a public
production seam would be added only for test convenience, or the expected
result must be changed merely to match current code.

## Output Contract

Return the selected mode and reason, requirement/acceptance or regression trace,
implemented cases, changed test paths, RED/GREEN or equivalent mode evidence,
focused and required check results, inherited and introduced failures, uncovered
scope, and unresolved items. When part of a work package, populate the
`agent-task-result/v2` evidence fields.
