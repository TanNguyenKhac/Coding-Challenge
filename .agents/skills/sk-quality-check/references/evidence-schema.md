# Development Evidence Schema

Use the project-defined `development-evidence/v1` envelope for persisted
verification evidence. This schema records decisions, actions, observations,
and proof; it must not contain chain-of-thought, credentials, or raw sensitive
provider payloads.

```json
{
  "schema": "development-evidence/v1",
  "run_id": "RUN-001",
  "repository_revision": "<full-git-sha>",
  "task_id": "TASK-001",
  "requirement_ids": ["REQ-API-001"],
  "decision_ids": ["ADR-0001"],
  "agent_role": "reviewer",
  "skills": [
    {
      "name": "sk-quality-check",
      "definition_revision": "<git-sha>"
    }
  ],
  "test_case_ids": ["TC-API-001"],
  "commands": [
    {
      "command": "<exact command>",
      "exit_code": 0
    }
  ],
  "artifacts": [],
  "status": "passed",
  "limitations": []
}
```

Use `passed`, `failed`, `blocked`, or `not-evaluated` for evaluated scopes. Do
not omit failed, skipped, blocked, or unexecuted required checks. Artifact entries
must use the identifiers, checksums, and provenance fields required by the
accepted artifact contract; this reference does not invent that contract.
