# 03. Agent Roles & Sandbox Boundaries

## 1. Specialized Agent Profiles in `.codex/agents/`

Instead of relying on a single "jack-of-all-trades" agent that tries to discover, code, test, and review in one bloated session, the repository defines 4 specialized agent profiles with strict sandbox boundaries:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                      SPECIALIZED AGENT PROFILES                        │
├─────────────────┬───────────────────┬──────────────────────────────────┤
│ Agent Profile   │ Sandbox Mode      │ Governing Skill                  │
├─────────────────┼───────────────────┼──────────────────────────────────┤
│ architect       │ workspace-write*  │ $sk-solution-design              │
│ backend-dev     │ workspace-write   │ $sk-backend-engineering,         │
│                 │                   │ $sk-test-engineering             │
│ ai-dev          │ workspace-write   │ $sk-ai-engineering,              │
│                 │                   │ $sk-test-engineering             │
│ reviewer        │ read-only         │ $sk-quality-check,               │
│                 │                   │ $sk-release-check                │
└─────────────────┴───────────────────┴──────────────────────────────────┘
* architect write access is restricted to docs/ and artifacts/handoffs/.
```

---

## 2. Agent Responsibilities & Invariants

### 2.1. `architect` (Discovery & Architecture Specialist)
- **Configuration**: `.codex/agents/architect.toml`
- **Purpose**: Analyze user requests, inspect repository context, design solutions, partition tasks into Work Packages, and identify risks.
- **Core Invariants**:
  - **CANNOT** edit application source code (`app/`), test suites (`tests/`), dependencies (`pyproject.toml`, `requirements.txt`), or databases.
  - Can only write proposal documents under `docs/` and handoff contracts under `artifacts/handoffs/`.
  - Cannot approve its own designs (must pause at Gate H1 for human sign-off).
  - When encountering missing business rules or architectural forks, it must stop and return `needs-input` with one clear clarifying question.

### 2.2. `backend-dev` (Backend & Persistence Engineer)
- **Configuration**: `.codex/agents/backend-dev.toml`
- **Purpose**: Implement assigned backend work packages (FastAPI endpoints, SQLAlchemy models, Celery async workers, Redis state) and matching tests.
- **Core Invariants**:
  - Allowed to modify only files listed in the package's `allowed_paths`.
  - Preserves existing user modifications.
  - Distinguishes pre-existing baseline test failures from newly introduced failures.
  - Captures fresh, deterministic test evidence before submitting `agent-task-result/v2`.

### 2.3. `ai-dev` (AI Pipeline & Media Generation Engineer)
- **Configuration**: `.codex/agents/ai-dev.toml`
- **Purpose**: Implement LangGraph StateGraph pipelines, prompt templates, Pydantic chemistry script schemas, TTS speech timeline alignment, and HTML animation layouts.
- **Core Invariants**:
  - Encapsulates external LLM/TTS provider integrations behind repository-owned interfaces (Dependency Inversion).
  - Uses **Test Seams** (deterministic mock stubs) for automated tests to avoid incurring API costs during continuous test execution.
  - Pauses before executing high-risk external actions (Gate H2) unless explicit authorization is provided.

### 2.4. `reviewer` (Independent Verification Specialist)
- **Configuration**: `.codex/agents/reviewer.toml`
- **Purpose**: Perform unbiased, independent verification of immutable candidates against approved specifications and acceptance criteria.
- **Sandbox Mode**: **Strictly `read-only`**.
- **Core Invariants**:
  - **CANNOT** edit candidate source files, tests, plans, or documentation.
  - Runs all required checks in a clean sandbox to capture independent proof.
  - Evaluates every acceptance criterion individually.
  - If tests fail, logs blocking findings into `reviewer-result/v2` to trigger a fix loop rather than altering code or assertions.

---

## 3. Why the Reviewer Must Strictly Be `read-only`

A critical architectural flaw in naive multi-agent systems is granting write permissions to the reviewing agent. This introduces the **"Self-Grading Student" Anti-Pattern**:

```text
               ┌───────────────────────────────────────────────────────────┐
               │         CONSEQUENCES OF A WRITABLE REVIEWER               │
               ├───────────────────────────────────────────────────────────┤
               │ 1. When tests fail, the reviewer edits tests to PASS.     │
               │ 2. Strips out safety assertions and validation checks.    │
               │ 3. Conceals subtle regression bugs from the engineer.     │
               │ 4. Completely corrupts verification integrity.            │
               └───────────────────────────────────────────────────────────┘
```

**The Harness Solution**:
1. Enforce `sandbox_mode = "read-only"` for `reviewer`.
2. When a check fails, the reviewer is physically unable to alter the test file. It must record a `blocking_finding` in `reviewer-result/v2`.
3. The workflow then routes the issue into a controlled **Fix Loop**, dispatching a targeted work package back to `backend-dev` or `ai-dev`.

---

## 4. The Single-Writer Rule & Disjoint Mutable Paths

When multiple subagents collaborate in parallel, uncoordinated file edits inevitably lead to lost code, race conditions, and corrupted states.

```text
                                 DISCOVERY CONTRACT
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
          Work Package PKG-01                         Work Package PKG-02
          Agent: backend-dev                          Agent: ai-dev
          Allowed Paths:                              Allowed Paths:
          - app/api/video.py                          - app/pipeline/graph.py
          - app/models/video.py                       - app/schemas/script.py
          - tests/integration/test_video_api.py       - tests/unit/test_script_schema.py
                   │                                           │
                   ▼                                           ▼
          [100% Parallel Safe]                        [100% Parallel Safe]
          Zero path overlap                           Zero path overlap
```

### Golden Rules of Parallel Execution:
1. **Single-Writer Rule**: Only one agent may write to a specific file at any given moment.
2. **Disjoint Mutable Paths**: The set of writable paths (`allowed_paths`) across concurrently executing packages must be mutually exclusive ($Paths_A \cap Paths_B = \emptyset$).
3. **Shared Contracts Defined Upfront**: Common interfaces (e.g., Pydantic schemas, shared database models) must be stabilized during Phase 1 (`wf-discover`) before concurrent developers begin implementation.
