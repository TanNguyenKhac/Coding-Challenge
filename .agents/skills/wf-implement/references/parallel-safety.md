# Parallel Safety

Parallel execution is optional. Two packages may run concurrently only when all
of these predicates are demonstrated:

- neither depends on output the other has not produced;
- their allowed paths are disjoint;
- they do not modify a shared contract, dependency manifest, or generated
  lockfile;
- they do not share mutable databases, fixtures, ports, sandboxes, or external
  resources;
- every interface between them is approved and frozen;
- integration order is deterministic; and
- the coordinator is the single integration owner.

If independence cannot be demonstrated, run sequentially. Agent specialization
does not itself establish independence.

Typical routing:

| Situation | Execution |
| --- | --- |
| Backend produces a contract consumed by an AI adapter | Backend first, freeze the contract, then AI |
| Disjoint persistence and prompt paths consume an already-frozen interface | Parallel is allowed if resources are isolated |
| Both packages change one manifest or lockfile | Sequential |
| Both use one non-isolated integration database | Sequential |

After concurrent packages finish, validate each result against its dispatch
identity, integrate in the predetermined order, and run whole-candidate checks.
Stop on conflicting diffs or stale identities; do not auto-merge blindly.
