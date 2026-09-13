---
name: sk-ai-engineering
description: Use when an implementation task changes model, provider, prompt, retrieval, tool, structured-output, evaluation, caching, fallback, or AI cost behavior.
---

# AI Engineering

Implement the smallest approved AI-enabled slice through provider-neutral,
typed boundaries with deterministic tests and traceable evidence.

## Mode Routing

- For provider ports, failures, timeouts, retries, caching, and cost controls,
  read `references/provider-and-cost.md`.
- For structured I/O, validation, deterministic fixtures, and evaluation, read
  `references/structured-output-and-evaluation.md`.
- For prompt and model revisions, read `references/prompt-model-versioning.md`.
- For repository-specific procedures, read `references/project-extension.md`.

Read only the references required by the current task.

## Inputs And Invariants

Require an approved input/output/failure contract, observable acceptance
criteria, allowed paths, declared test mode, verified capabilities, and
repository-owned checks. The evaluation oracle or rubric must come from the
approved plan or repository; do not invent it.

Application logic depends on an application-owned port, not a provider SDK.
Use typed inputs, outputs, and failures, validate structured output before domain
use, and keep provider and repository domain details behind their owned
interfaces.

## Procedure

1. Inspect the approved contract, capability evidence, and established
   repository patterns.
2. Select only relevant references and preserve provider-neutral boundaries.
3. Use `$sk-test-engineering` with deterministic fakes or fixtures and the
   declared test mode. Real provider calls are off by default.
4. Implement one coherent diff inside allowed paths, including explicit
   timeout, retry/backoff, rate-limit, fallback, idempotency, cache, and cost
   semantics when the approved contract requires them.
5. Validate outputs before downstream use and map failures into repository-owned
   categories.
6. Run focused and required checks, self-review the diff, and record applicable
   prompt, model, provider, tool, schema, cache, and evaluation revisions.

## Stop Conditions

Stop on unverified capability, missing schema or evaluation oracle, unresolved
failure/fallback/caching semantics, unknown credential or data boundary,
unapproved public-contract change, paid or production action without matching
H2, path conflict, or required work outside the package.

## Output Contract

When invoked with `work-package/v2`, return `agent-task-result/v2` with changed
paths, requirement and acceptance trace, test and evaluation evidence, exact
commands and exit codes, revision and provenance data, external actions,
self-review, concerns, and deviations. Do not represent fake evidence as a real
call or apply an unapproved contract delta.
