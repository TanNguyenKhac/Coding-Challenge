# Task Contract

Use the canonical schemas in
[`docs/workflows/handoff-contracts.md`](../../../../docs/workflows/handoff-contracts.md).
Do not redefine them in a prompt or another artifact.

## Compile A Work Package

Create one `work-package/v2` for a coherent behavior slice that one agent can
implement and prove in one invocation. Do not split mechanical changes of the
same shape merely to create more tasks.

Each package must:

- trace to approved requirements, observable acceptance criteria, and relevant
  decisions;
- name one owner and explicit allowed and forbidden paths;
- declare dependencies and consumed or produced interfaces;
- select one test mode and repository-owned focused checks;
- record known baseline failures, H2 triggers, stop conditions, a finite retry
  limit, and its evidence destination.

Commands must come from repository authority, CI, package scripts, or an
established validation owner. Do not guess a plausible command.

For `fix`, include only the supplied verification findings and their matching
tests. Route back to discovery/H1 when a finding requires new product or design
authority.

## Dispatch Brief

Send the package path or exact contract, its repository authority and context
refs, known baseline failures, and the required `agent-task-result/v2` output
schema. Do not include unrelated chat history or adjacent packages. For Codex
spawns, set `fork_turns: "none"` and supply only this brief; on another runtime,
use the equivalent no-inherited-history option. One meaningful package gets one
fresh agent invocation. Retain the returned agent identifier and use that same
invocation for retrieval or bounded follow-up.

## Accept A Result

Parse the result and validate all of the following against current repository
state:

- the run, task, owner, attempt, and status match the dispatched package;
- all changed paths are allowed and no protected action occurred before H2;
- requirement and acceptance trace remains complete;
- evidence matches the declared test mode and includes exact commands,
  timestamps, exit codes, and useful output summaries or artifact refs;
- the base and result identities still match the inspected diff or manifest;
- self-review reports no unrelated changes or sensitive output.

Do not complete a task from an agent claim alone. `done-with-concerns` requires
an explicit coordinator disposition. A missing, interrupted, failed, malformed,
or null result is `needs-context`, `blocked`, or `failed`, never `done`.
