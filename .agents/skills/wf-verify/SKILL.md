---
name: wf-verify
description: Coordinate independent read-only verification of a fixed software candidate through the project reviewer, optionally including release readiness, and stop for H3 acceptance. Use after implementation or whenever a specific candidate revision needs evidence-backed verification.
---

# Verify Workflow

Coordinate independent verification; do not repair the candidate.

1. Read `AGENTS.md`, `docs/WORKFLOW.md`, the implementation handoff, fixed
   candidate identity, required checks, acceptance criteria, and supplied
   rubrics.
2. Return `blocked` when the candidate is not fixed or required inputs are
   absent.
3. Before delegation, identify the available spawn and wait/inspect operations.
   Delegate exactly one bounded task to the project custom agent `reviewer`,
   capture its returned identifier, and require `$sk-quality-check` for every run
   and `$sk-release-check` only when `release_required=true`.
4. Retrieve that same agent with wait, inspect, or follow-up operations. Never
   spawn a replacement merely because retrieval is delayed. If the result
   cannot be retrieved, return `blocked`.
5. Require the reviewer to record repository state before and after checks and
   to remain read-only. It must report failures and skipped checks rather than
   fix them.
6. Treat a missing, interrupted, failed, malformed, or null reviewer result as
   `blocked`, never as passed.
7. If verification fails, recommend a bounded fix task through `$wf-implement`
   and require a new candidate before rerunning verification.
8. Stop at H3 and ask the human to `accept`, `accept-with-conditions`,
   `return-for-fix`, `release`, or `reject`. Bind the decision to the verified
   candidate revision.

Read `../../../docs/workflows/handoff-contracts.md` for the verification handoff
and H3 requirements.
