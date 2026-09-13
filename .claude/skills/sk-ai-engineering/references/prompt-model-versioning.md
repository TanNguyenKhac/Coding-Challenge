# Prompt and Model Versioning

Use this reference when a change affects instructions, templates, model
selection, model parameters, or tool descriptions.

## Required Authority

Locate the accepted behavior, model-selection ownership, compatibility policy,
and rollback expectations. A provider default does not establish repository
policy.

## Procedure

- Give maintained prompts and templates stable revision identifiers.
- Keep model selection and parameters explicit at the approved ownership layer.
- Record which prompt, model, parameters, tools, and schema produced evaluated
  outputs.
- Preserve a rollback path for behaviorally significant revisions.
- Use representative deterministic fixtures where possible and disclose
  nondeterministic coverage.

Stop when selection ownership, compatibility, evaluation criteria, or rollback
behavior is unresolved.
