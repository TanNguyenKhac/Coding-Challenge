---
name: sk-release-check
description: Perform evidence-based security and delivery-readiness reviews before a demo, submission, or release. Inspect architecture, configuration, dependencies, runbooks, artifacts, and clean-path execution; report ready, conditional, or blocked without silently fixing findings or claiming checks that were not run.
---

# Release Check

## Outcome

Produce a defensible `ready`, `conditional` or `blocked` verdict backed by
security findings, clean-path evidence, artifact provenance and disclosed gaps.

## Modes

- `security-review`: review trust boundaries, credentials, inputs, tools,
  dependencies, logs and artifact access.
- `delivery-readiness`: verify setup, migration, startup, execution, recovery,
  runbook and artifact reproducibility.
- `combined-release-gate`: perform both when explicitly requested or required by
  the accepted release contract.

## Authority

- Accepted requirements and architecture decisions
- Threat model and security boundary
- Dependency and configuration manifests
- Acceptance contract and required checks
- Application runbook and artifact policy

## Default Boundary

Operate read-only. If a runbook or manifest change is useful, propose exact
hunks and wait for approval before applying only those documentation changes.
Do not repair application code or downgrade a finding.

## Procedure

1. Record the release scope, repository revision and environment.
2. Select only the requested or required mode.
3. Review evidence for applicable trust boundaries and high-risk operations.
4. Execute the documented clean path when the environment and authorization
   permit it.
5. Verify setup, migrations, services, recovery steps, outputs and checksums.
6. Classify findings by severity and readiness impact.
7. Issue a verdict with required actions and explicit limitations.

## Stop Conditions

Return `blocked` when:

- the required clean-path replay was not executed;
- a critical environment, credential or service is unavailable;
- artifact provenance or checksum is missing;
- migration or rollback evidence required by the release contract is absent;
- a critical or high finding has no accepted disposition;
- important security evidence cannot be inspected.

## Output Contract

- Release ID, scope, revision and environment
- `ready`, `conditional` or `blocked` verdict
- Security findings with evidence and severity
- Readiness checks with observed results
- Artifact identifiers and checksums
- Known limitations, required actions and owners

## Verdict Rules

- `ready`: all required checks passed and no unresolved blocker remains.
- `conditional`: only disclosed limitations with authorized acceptance remain.
- `blocked`: required proof is missing or a blocker remains unresolved.

## Validation

- Never claim a check ran when it did not.
- Never call an environment clean unless setup began from the defined baseline.
- Every finding contains evidence and affected scope.
- Every required action has an owner or is explicitly unassigned.
- Repository changes respect the default read-only boundary.
