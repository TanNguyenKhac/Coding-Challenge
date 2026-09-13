# Test Modes

Choose one mode for each work package. The choice affects required evidence; it
does not weaken the requirement for an approved oracle and fresh command proof.

## TDD

Use for new observable behavior or a bug fix with a reliable oracle.

1. Add the smallest test that expresses the approved behavior.
2. Run it and confirm RED fails for the intended missing behavior, not syntax,
   fixture, import, or environment failure.
3. Record the RED command, time, exit code, and output summary.
4. Implement the minimum behavior, run GREEN, then refactor while preserving
   GREEN.

## Characterization

Use before changing legacy internals whose current accepted behavior must remain
stable. Capture the current observable baseline, add cases for the affected
boundary, then refactor and rerun them. A characterization test does not turn an
undocumented accident into product authority; stop if the desired behavior is
in dispute.

## Contract

Use for interfaces, providers, schemas, protocols, or serialization boundaries.
Exercise accepted valid, boundary, malformed, incomplete, and rejected shapes
against the real boundary or a faithful fake. Assert externally visible results
and failure categories, not only collaborator calls.

## Verification-Only

Use for documentation, configuration, generated artifacts, or changes where a
test-first cycle adds no useful signal. State why, then run the smallest
repository-native lint, parse, build, rendering, snapshot, or inspection command
that observes the changed artifact.

## Not Applicable

Use only when no executable or inspectable behavior exists. Record the reason,
the manual or structural evidence used instead, and any unverified risk. Do not
use this mode to bypass an available oracle or a failing check.

## Evidence Rules

- Every case traces to approved requirement/acceptance refs or a supplied
  regression symptom.
- Commands, timestamps, exit codes, and useful output summaries or artifact
  refs are reproducible and sanitized.
- Report inherited failures separately from introduced failures.
- Do not change an expected result or quality threshold merely to make code
  pass, and do not add an unapproved public production seam for test access.
