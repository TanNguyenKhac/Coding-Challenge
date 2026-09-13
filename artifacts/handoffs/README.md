# Handoffs

Persist approved workflow handoffs here only when the task requires a durable
artifact. Include the schema version, change ID, repository or candidate
revision, gate status, and referenced evidence.

Place change-scoped records under `handoffs/<change-id>/`. New WF2 runs emit
`implementation-handoff/v2`; `implementation-handoff/v1` is legacy input only.
