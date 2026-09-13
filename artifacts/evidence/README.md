# Evidence

Persist approved verification evidence here. Keep exact commands, exit codes,
artifact identities, checksums, limitations, and failed or skipped checks
visible. Do not store credentials or chain-of-thought.

Durable WF2 runs use a digest-bound preflight snapshot,
`evidence/<change-id>/progress.json`, one task evidence file per work package,
final-check evidence, and a digest-bound candidate content manifest when the
candidate is not a commit. Evidence must not contain raw sensitive payloads.
