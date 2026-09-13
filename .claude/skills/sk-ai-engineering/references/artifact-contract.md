# Generated Artifact Contract Procedure

Use this reference for generated HTML, audio, timeline, and video metadata,
storage, provenance, checksums, and retrieval references.

## Required Authority

Locate the accepted artifact types, storage root or service, identifier and URI
rules, access boundary, retention/cleanup policy, manifest schema, and sensitive
content handling. A locally convenient directory is not automatically the
product artifact policy.

## Required Traceability

For each artifact, preserve the fields required by the accepted contract. These
commonly include—but are not established merely by this reference—the artifact
identifier, type, URI, checksum, creation time, input identity, provider and
template revision, timing metadata, and producing task/run identity.

## Implementation Proof

- Compute checksums from the final stored bytes.
- Verify that the returned reference resolves through the approved retrieval
  boundary.
- Keep temporary/intermediate outputs distinct from committed deliverables.
- Exercise missing, incomplete, corrupt, duplicate, and cleanup behavior when
  those cases are in scope.
- Do not persist credentials or raw sensitive provider payloads.

Stop when storage, URI semantics, access, retention, provenance fields, or
sensitive-content handling is unresolved.
