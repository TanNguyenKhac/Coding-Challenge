# 02. Defining Skills & Orchestrating Workflows

## 1. Standard Skill Directory Structure in `.agents/skills/`

Every skill in the repository follows a modular, version-controlled, and extensible layout:

```text
.agents/skills/<skill-name>/
├── SKILL.md                 # Core instructions, governance procedures, and execution rules
├── agents/
│   └── openai.yaml          # Tool mappings and runtime definitions for OpenAI/Codex CLI
├── references/              # Deep domain references loaded on demand (Context-efficient)
│   ├── contract-schema.md
│   └── implementation-rules.md
└── scripts/                 # Automated verification or evidence extraction scripts
    └── validate_evidence.py
```

### 1.1. Anatomy of `SKILL.md`
Each `SKILL.md` file begins with standard YAML frontmatter defining `name` and `description` (used by CLI tools to surface relevant capabilities), followed by structured engineering steps:

```markdown
---
name: sk-backend-engineering
description: Use when an implementation task changes server-side interfaces, state, persistence, asynchronous processing, reliability, or recovery behavior.
---

# Backend Engineering

Governing procedure for backend changes...

## Inputs
...
## Workflow & Rules
...
## Completion Standard
...
```

### 1.2. The `references/` Directory (Targeted Context Loading)
To prevent `SKILL.md` from overflowing the agent's context window, deep technical domain knowledge is modularized into `references/`. The agent loads these files only when working on matching sub-problems:
- Example from `sk-ai-engineering`:
  - `references/html-composition.md`: Layout guidelines for chemistry animation HTML/CSS components.
  - `references/speech-timeline.md`: Algorithms for aligning TTS speech duration with visual video frames.
  - `references/structured-output-and-evaluation.md`: Pydantic schema enforcement patterns and LLM output parsing/retry strategies.

---

## 2. Skill Taxonomy in the Repository

Skills are categorized into three functional groups:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                             SKILL TAXONOMY                             │
├──────────────────────────────────┬─────────────────────────────────────┤
│ 1. ORCHESTRATION (WORKFLOWS)     │ wf-discover, wf-implement, wf-verify │
├──────────────────────────────────┼─────────────────────────────────────┤
│ 2. CAPABILITY (DOMAIN SKILLS)    │ sk-solution-design                  │
│                                  │ sk-backend-engineering              │
│                                  │ sk-ai-engineering                   │
│                                  │ sk-test-engineering                 │
│                                  │ sk-quality-check                    │
│                                  │ sk-release-check                    │
├──────────────────────────────────┼─────────────────────────────────────┤
│ 3. PLATFORM & MAINTENANCE        │ improve-harness                     │
│                                  │ encode-invariant                    │
│                                  │ git-add-commit                      │
└──────────────────────────────────┴─────────────────────────────────────┘
```

### 2.1. Capability Skills (Domain Knowledge)

1. **`$sk-solution-design`**:
   - Solution architecture specialist. Classifies incoming requests into **Spike** (exploratory prototype), **Bounded Change** (localized modification), or **Architectural Change** (multi-subsystem revision).
   - Establishes `affected_areas`, `acceptance_criteria` with explicit oracles, and identified `risks`.
2. **`$sk-backend-engineering`**:
   - Implements FastAPI REST endpoints, SQLAlchemy transaction models, Celery/Redis asynchronous workers, and fault-recovery mechanics (idempotency, dead-letter queues, retries).
3. **`$sk-ai-engineering`**:
   - Constructs LangGraph StateGraph pipelines, prompt versioning schemas, Pydantic structured output models, TTS speech timeline synchronization, and chemistry visualization components.
4. **`$sk-test-engineering`**:
   - Builds **Test Seams** (deterministic mocks/stubs) for external APIs (LLMs, TTS, video rendering), authored unit tests, integration tests, and end-to-end suites.
5. **`$sk-quality-check`**:
   - Evaluates code health, static analysis (flake8, mypy, black), test coverage, regression detection, and verification evidence integrity.
6. **`$sk-release-check`**:
   - Validates release readiness: database migrations, `.env` configurations, operational runbooks, and secret management boundaries.

---

## 3. The 3-Phase Workflow Lifecycle & Human-in-the-Loop Gates (H1, H2, H3)

All modifications undergo a three-phase lifecycle to ensure safety and precision:

```text
[Incoming User Request]
       │
       ▼
 ┌─────────────┐
 │ wf-discover │ ──► Delegates to `architect` (Explore, plan, design handoff)
 └─────────────┘
       │
       ▼
 ╔═════════════╗
 ║   GATE H1   ║ ◄── Human approves Architecture, Scope, and Acceptance Criteria
 ╚═════════════╝
       │ (Approved)
       ▼
 ┌─────────────┐
 │wf-implement │ ──► Delegates to `backend-dev` / `ai-dev` (Write code + tests)
 └─────────────┘
       │
       ├────────► [If high-risk action: migration, data wipe, paid external API call]
       │                 │
       │                 ▼
       │          ╔═════════════╗
       │          ║   GATE H2   ║ ◄── Human explicitly authorizes high-risk action
       │          ╚═════════════╝
       ▼
 ┌─────────────┐
 │  wf-verify  │ ──► Delegates to `reviewer` (Read-only, independent evaluation)
 └─────────────┘
       │
       ▼
 ╔═════════════╗
 ║   GATE H3   ║ ◄── Human reviews Verification Evidence & authorizes Merge/Release
 ╚═════════════╝
       │
       ▼
  [Completed]
```

### Detailed Phase Breakdown:

#### Phase 1: `$wf-discover` (Discovery & Architecture Design)
- **Agent**: `architect` (governed by `$sk-solution-design`).
- **Sandbox Boundary**: Allowed only to inspect the repository and write to `docs/` and `artifacts/handoffs/`. Cannot edit application code or tests.
- **Output**: `artifacts/handoffs/<CHANGE_ID>-discovery.yaml` (schema `discovery-handoff/v2`).
- **Gate H1 (Human Gate 1)**: The engineer inspects proposed requirements, affected paths, and acceptance criteria. Development starts only upon explicit approval.

#### Phase 2: `$wf-implement` (Implementation & Bounded Development)
- **Agents**: `backend-dev` and/or `ai-dev` (governed by `$sk-backend-engineering`, `$sk-ai-engineering`, `$sk-test-engineering`).
- **Sandbox Boundary**: Strict enforcement of `allowed_paths` declared in each Work Package contract.
- **Gate H2 (Human Gate 2)**: Execution pauses before any high-risk action (destructive migrations, secret access, paid live API calls).
- **Output**: Implementation code, automated tests, and local test run outputs (`agent-task-result/v2`).

#### Phase 3: `$wf-verify` (Independent Verification)
- **Agent**: `reviewer` (governed by `$sk-quality-check`, `$sk-release-check`).
- **Sandbox Boundary**: Strictly **`read-only`**. The reviewer executes the complete test suite independently, matches results against Acceptance Criteria, and scans for regressions.
- **Gate H3 (Human Gate 3)**: The engineer reviews the comprehensive `reviewer-result/v2` report and verified execution evidence (`artifacts/evidence/`) to authorize release or merge.

---

## 4. Handoff Contracts & Safe Execution

State between workflow phases is preserved through structured YAML contracts in `artifacts/handoffs/` (governed by `docs/workflows/handoff-contracts.md`):

### Example `discovery-handoff/v2` Contract:
```yaml
schema: discovery-handoff/v2
change_id: CHG-002
status: ready-for-approval
repository_mode: brownfield
base_revision: "cbe20dd"
requirements:
  - id: REQ-01
    title: "Implement Pydantic Chemistry Video Script Schema"
acceptance_criteria:
  - id: AC-01
    title: "LLM generates valid JSON containing scenes and visual_elements list"
    oracle: "pytest tests/unit/test_script_schema.py passes"
work_packages:
  - id: PKG-01
    agent: ai-dev
    allowed_paths:
      - "app/schemas/script.py"
      - "app/pipeline/nodes/script_node.py"
      - "tests/unit/test_script_schema.py"
risks:
  - id: RSK-01
    description: "LLM output might wrap JSON in markdown backticks causing parse failure"
    mitigation: "Use LangChain JsonOutputParser with sanitization regex"
```

### Why Handoff Contracts Work:
1. **Context Immunity**: When transitioning from Discovery to Implementation, the developer agent reads only the handoff file. There is zero need to re-feed thousands of chat tokens.
2. **Eliminates Path Pollution**: The `allowed_paths` block restricts the developer agent from altering unapproved files.
3. **Executable Verification Oracles**: Every acceptance criterion is paired with an unambiguous, automated test command (`oracle`).
