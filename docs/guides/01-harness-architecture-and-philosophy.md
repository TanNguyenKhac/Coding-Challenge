# 01. Harness Architecture & Core Philosophy

## 1. The Real-World Failure Modes of AI Coding (The "Vibe Coding" Trap)

As Frontier Large Language Models (LLMs) grow increasingly powerful, many engineers interact with AI through freeform, conversational prompting. However, in complex technical codebases like `chemistry-video-engine`—which integrates FastAPI, Celery/Redis, LangGraph AI orchestration, audio TTS timeline alignment, and Remotion/HTML video rendering—freeform prompting quickly breaks down into several severe failure modes:

```text
[Freeform Prompting / Ad-hoc Chat]
       │
       ├──► 1. Context Rot (Loss of context after 5-10 turns; AI forgets earlier invariants)
       ├──► 2. Hallucination (Invented API contracts, configs, or domain logic)
       ├──► 3. Scope Creep & Regression (Edits out-of-scope files; deletes tests to force a pass)
       └──► 4. Session Amnesia (Switching sessions or models loses all progress & rationale)
```

1. **Context Rot & Context Drift**:
   - As conversations grow, the model's context window fills with obsolete code snippets, error traces, and unstructured chit-chat.
   - The model forgets foundational architectural constraints and begins proposing fragmented, contradictory patches.
2. **Hallucination & Fabricated Authority**:
   - Without explicit repository boundaries, AI models frequently invent business rules (e.g., guessing video duration limits, fabricating unapproved Pydantic script fields) rather than referencing repository specs or asking the user.
3. **Over-engineering & Breaking Invariants**:
   - When encountering a failing test, models often attempt wide-scale refactoring across unrelated modules, or worse: **modify or delete the test assertions** to make the suite pass instead of addressing the root bug.
4. **Session Amnesia**:
   - Ephemeral conversational state is lost when opening a fresh session or switching agents. The engineer is forced to repeatedly re-explain the entire architectural context.

---

## 2. The Essence of the Harness Layer

The **Harness Layer** is a disciplined system of boundary enforcement, typed handoff contracts, and guided workflows checked directly into the repository to **constrain AI behavior into standard software engineering practices**.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        HARNESS LAYER PHILOSOPHY                        │
├────────────────────────────────────────────────────────────────────────┤
│ 1. REPOSITORY AS SYSTEM OF RECORD                                      │
│    All specs, plans, code, tests, and evidence reside in Git.          │
│    Zero dependency on external, opaque agent task databases.          │
├────────────────────────────────────────────────────────────────────────┤
│ 2. SEPARATION OF CONCERNS (3-PHASE LIFECYCLE)                          │
│    Discover (Architect) ──► Implement (Devs) ──► Verify (Reviewer)     │
│             │                        │                      │          │
│             ▼                        ▼                      ▼          │
│          Gate H1                  Gate H2                Gate H3       │
│    (Human Approval)          (Risk Checkpoint)       (Release Gate)    │
├────────────────────────────────────────────────────────────────────────┤
│ 3. EVIDENCE OVER CLAIMS                                                │
│    Claims of completion are rejected without fresh, executable test    │
│    outputs and deterministic artifact evidence.                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.1. Repository as System of Record (Git is the Single Source of Truth)
- The Harness maintains no parallel external database (such as external SQLite task tables or separate orchestration servers).
- All operational state is expressed as standardized, version-controlled repository artifacts:
  - **Governing Rules**: `AGENTS.md`, `CLAUDE.md`, `docs/WORKFLOW.md`.
  - **Product Specifications & Requirements**: `docs/product/overview.md`, `docs/specs/`.
  - **Durable Working Memory**: `docs/plans/active/` (in-flight changes) and `docs/plans/completed/` (verified & completed changes).
  - **Inter-phase Handoff Contracts**: `artifacts/handoffs/` (structured YAML contracts between phases).
  - **Execution Evidence**: `artifacts/evidence/` (command logs, test results, execution hashes).

### 2.2. Single-Writer & Disjoint Mutable Paths
- For any given task or work package, exactly one agent possesses write access (`Single-writer`).
- When executing tasks concurrently, subagents must operate on strictly non-overlapping file sets (`Disjoint mutable paths`), eliminating merge conflicts and race conditions.

### 2.3. Independent Responsibilities: Developer vs. Reviewer
- Coding agents (`backend-dev`, `ai-dev`) run with `workspace-write` capabilities within assigned paths but **have no authority to certify their own work**.
- The evaluating agent (`reviewer`) operates strictly in **`read-only`** mode. The reviewer independently runs verification commands, inspects diffs, and checks acceptance criteria without being able to mutate code or tests to force a passing verdict.

---

## 3. Comparative Analysis: Freeform Prompting vs. Harness-Driven Engineering

| Dimension | Freeform Prompting / Ad-hoc Chat | Harness-Driven AI Engineering |
| :--- | :--- | :--- |
| **Context Management** | Dumps entire files into the prompt; leads to prompt bloat, high cost, and context rot. | Strict file boundaries; agents only inspect authorized context references (`context_refs`). |
| **Domain Accuracy** | Model hallucinates configurations and schemas when information is missing. | Grounded in `docs/specs/`; halts and queries the user (`needs-input`) upon encountering ambiguities. |
| **Stability & Regression** | Edits break existing modules; model modifies test files to fake green tests. | Enforces architectural invariants (`docs/patterns/encoding-invariants.md`); distinguishes baseline vs. introduced failures. |
| **Recovery & Continuity** | Session crash or context limit wipes all working memory. | Resumes instantly from durable plan files (`docs/plans/active/`) and handoff contracts. |
| **Completion Standard** | "I have fixed the issue" (Unsubstantiated conversational claim). | Verifiable execution proof: fresh `pytest` outputs, logs, and artifacts recorded in `artifacts/evidence/`. |
| **Human Control** | Engineer reviews code after the AI has already altered dozens of files arbitrarily. | Proactive human governance at 3 explicit gates (H1: Plan Approval, H2: Risk Confirmation, H3: Release Sign-off). |

---

## 4. Case Study: Building `chemistry-video-engine`

Consider implementing a critical feature: **Adding Chemical Safety Validation into the LangGraph Video Script Pipeline**:

```text
               REQUEST: "Add safety warnings for hazardous chemical reactions"
                                         │
       ┌─────────────────────────────────┴─────────────────────────────────┐
       ▼                                                                   ▼
[Freeform Prompting Approach]                                  [Harness-Driven Approach]
1. Prompt: "Add safety checks to the app"                      1. Run `$wf-discover`:
2. AI immediately modifies `main.py` and changes                  - `architect` inspects `docs/specs/SPEC-03-llm-structured-script.md`
   the LLM output schema arbitrarily.                             - Identifies needed Pydantic schema changes (`safety_warnings`)
3. Downstream modules (TTS audio generator &                       and a new `safety_validator` node in LangGraph.
   video renderer) crash due to schema mismatch.                  - Emits discovery handoff v2 and pauses at **Gate H1**.
4. When unit tests fail, the AI edits the test suite           2. Human approves H1 ──► Run `$wf-implement`:
   to delete the validation assertions.                           - `ai-dev` updates schemas & state graph within `allowed_paths`.
5. OUTCOME: Unstable system, broken contracts,                     - Captures deterministic pytest logs in `artifacts/evidence/`.
   and hidden regressions.                                     3. Run `$wf-verify`:
                                                                  - `reviewer` (read-only) runs full test suite independently.
                                                                  - Verifies all acceptance criteria and submits report at **Gate H3**.
                                                               4. OUTCOME: Rock-solid implementation, updated specs, 100% test coverage.
```

---

## 5. Supercharging Brainstorming & Architecture Design

The Harness Layer is not merely an implementation runner; it is a powerful architectural brainstorming framework:

1. **Safe Exploration Without Code Pollution**:
   - During `$wf-discover`, the `architect` agent operates exclusively in read-only inspection mode (writing only to `docs/` or `artifacts/handoffs/`).
   - You can evaluate competing technical strategies (e.g., comparing Remotion vs. Manim rendering engines) without risking accidental code modifications.
2. **Explicit Fact Classification**:
   - The architect is required to classify all information into five explicit tiers:
     * **Authoritative**: Established by approved documentation or repository decisions.
     * **Observed**: Current runtime code behavior.
     * **Derived**: Logical deduction from existing facts.
     * **Decision Required**: Ambiguity requiring human judgment.
     * **Unknown**: Missing information that must be clarified.
   - This eliminates implicit assumptions and exposes design flaws before any code is written.
