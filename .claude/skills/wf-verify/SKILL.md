---
name: wf-verify
description: Use when independently verifying an immutable implementation candidate against its approved acceptance and release contract before H3.
---

# Verify

Independently verify one immutable candidate and produce an evidence-backed H3
package. Never modify the candidate or perform a release action.

## Inputs

Require `change_id`, `implementation_handoff_ref`, an exact `candidate_ref`, and
`release_required`. Load the approved verification contract from the discovery
handoff.

## Procedure

1. Read repository authority, `references/verification-procedure.md`, and
   `../../../docs/workflows/handoff-contracts.md`.
2. Validate handoff chain, approval, candidate identity, unresolved items,
   required checks, rubric and release profile. Stop if any required input is
   missing, stale or contradictory.
3. Lock the candidate by full commit SHA or content-manifest hash. Snapshot its
   state before review.
4. Compile `verification-plan/v2` mapping every in-scope AC to checks/evidence and `verification-evidence/v1`. Apply
   apply only risk-triggered probes defined by repository policy.
5. Dispatch exactly one fresh-context `reviewer` task with candidate identity,
   base identity, approved contracts, plan and evidence locations. Do not pass
   implementation conversation history.
6. Require `$sk-quality-check` for all runs. Require `$sk-release-check` only
   when `release_required=true`.
7. Obtain fresh evidence for the exact candidate. Use an isolated runner or CI
   when commands need workspace writes; never grant reviewer mutation authority
   over the candidate.
8. Reject stale, partial, missing, rerun-until-green or candidate-mismatched
   evidence. A skipped/unknown required check is not a pass.
9. Validate the reviewer result, finding schema (including `verification-finding/v1`), AC coverage and pre/post
   candidate state. Null, interrupted or malformed results are blocked.
10. Emit `verification-handoff/v2` and stop at H3. On failure, create a bounded
    finding set for `wf-implement mode=fix`; do not patch it here.

## Stop conditions

Stop on candidate drift, broken handoff chain, missing oracle/rubric, required
check failure, unavailable required environment, unapproved external action,
evidence integrity failure, reviewer mutation, or malformed reviewer result.

Never self-approve H3, edit candidate files, lower thresholds after seeing
results, deploy, merge, publish, or claim release readiness without the
conditional release check.
