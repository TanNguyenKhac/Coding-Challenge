# Structured Output And Evaluation

Use this reference for typed generation inputs and outputs, prompt or tool
results, parsing, validation, deterministic fixtures, evaluation seams, and
quality evidence.

## Required Authority

Locate the approved schema, validation rules, required fields, repair or
fallback behavior, failure categories, evaluation oracle or rubric, thresholds,
and representative fixture policy. A provider response or model preference is
not an oracle.

## Implementation

- Preserve provider-neutral input, output, and failure types at the application
  boundary.
- Parse and validate all structured output before it enters the domain.
- Preserve validation failures as explicit repository-defined results.
- Apply repair, retry, or fallback only for approved triggers and stopping
  conditions.
- Expose evaluation through deterministic seams and use faithful fakes or
  fixtures for valid, boundary, malformed, incomplete, and unsupported output.

## Proof And Evidence

Contract tests cover parsing, validation, failure translation, and downstream
rejection. Evaluation records the approved rubric and input revisions, result,
and relevant prompt, model, provider, tool, and schema identities. Avoid tests
that only prove a mock was called, and never invent or relax a threshold to make
the candidate pass.

Stop when the schema, validation oracle, repair ownership, rubric, threshold, or
representative evidence policy is unresolved.
