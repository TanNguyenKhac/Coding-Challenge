# Command Verification

Use this reference to execute approved tests, builds, lint checks, and runtime
verification without modifying the implementation.

## Before Execution

- Identify the repository source that requires each command.
- Record the repository revision, working-tree state, environment, and command
  scope.
- Confirm prerequisites and whether the command can mutate caches, generated
  files, services, databases, or external systems.
- Do not run a command whose environment, credentials, cleanup ownership, or
  external effects are unresolved.

## Evidence

For each command record the exact invocation, working directory, result, exit
code, relevant output, and any produced artifact. Keep failed, skipped,
deselected, and not-run checks visible.

Use the command's documented result contract. A zero exit code proves only the
scope that command actually checks; it does not imply broader release or quality
readiness.

## Read-Only Check

Compare repository and relevant runtime state before and after execution. Report
unexpected changes as findings and do not clean them up unless separately
authorized.
