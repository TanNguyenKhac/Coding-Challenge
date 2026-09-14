# 04. Power Tips & Tricks for CLIs and Frontier Models

## 1. Matching Frontier Models to Workflow Phases

With the arrival of next-generation frontier reasoning models (Claude 3.7 Sonnet/Opus 5 with Extended Thinking, OpenAI o3/o1/GPT-4o, Gemini 2.0/3.7 Flash Thinking) and advanced CLI tools (**Claude Code** and **OpenAI Codex CLI**), pairing the right model with the right workflow phase yields exponential gains in speed and software quality.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                      PHASE-TO-MODEL ALIGNMENT                          │
├─────────────────┬──────────────────────────┬───────────────────────────┤
│ Phase / Task    │ Recommended Model        │ Core Capabilities         │
├─────────────────┼──────────────────────────┼───────────────────────────┤
│ Phase 1:        │ Claude 3.7 Thinking,     │ Deep reasoning, edge-case │
│ Discovery &     │ OpenAI o3/o1,            │ discovery, architectural  │
│ Brainstorming   │ Gemini 3.7 Flash Thinking│ boundary analysis.        │
├─────────────────┼──────────────────────────┼───────────────────────────┤
│ Phase 2:        │ Claude 3.7 Sonnet,       │ High-speed execution,     │
│ Implementation  │ GPT-4o, Gemini 2.0 Flash │ precise schema adherence, │
│ & Bounded Dev   │                          │ test seam authoring.      │
├─────────────────┼──────────────────────────┼───────────────────────────┤
│ Phase 3:        │ Claude 3.7 Thinking,     │ Adversarial review,       │
│ Independent     │ OpenAI o3/o1             │ zero tolerance for        │
│ Verification    │                          │ regression or fake tests. │
└─────────────────┴──────────────────────────┴───────────────────────────┘
```

---

## 2. Context Window Optimization & Prompt Caching

Dumping entire directories or large codebases into an LLM prompt degrades performance (Context Dilution), increases latency and costs, and causes the model to ignore critical instructions.

### Tip 1: Pinpoint Code Locations with `file_path:line_number`
- Use fast index tools (`Grep`, `Glob`) to locate exact files and functions. Read only the necessary slices using `offset` and `limit`.
- Reference code locations in plans and handoffs as `app/pipeline/graph.py:45` to maintain clickable, precise context without token waste.

### Tip 2: Maximize Provider Prompt Caching
- **Mechanism**: LLM APIs cache identical prompt prefixes across requests (System instructions, `AGENTS.md` rules, Skill definitions).
- **Practice**: Keep foundational rules static at the beginning of the prompt; append dynamic task arguments only at the end. This accelerates response times by 3–5x and cuts token costs by up to 90%.

---

## 3. Harnessing Extended Thinking & Reasoning Models

In complex domains like `chemistry-video-engine`—which demands chemical reaction validation, molecular equation balancing, visual scene duration alignment, and audio timeline synthesis—the deep reasoning capabilities of models like Claude 3.7 Thinking and o3-mini are essential.

```text
               GOAL: "Synchronize visual reaction scene with TTS audio duration"
                                         │
                                         ▼
                   ┌───────────────────────────────────────────┐
                   │     EXTENDED THINKING PROCESS (AI)        │
                   ├───────────────────────────────────────────┤
                   │ 1. Calculate word-per-minute TTS rate.    │
                   │ 2. Compute timestamp for chemical equation │
                   │    appearance: 2H2 + O2 -> 2H2O.          │
                   │ 3. Evaluate edge cases:                   │
                   │    - Fast narration (< 1.5s per scene).   │
                   │    - Long LaTeX chemical formulas.        │
                   │ 4. Formalize strict Pydantic models.      │
                   └───────────────────────────────────────────┘
                                         │
                                         ▼
                     [Flawless, Bulletproof Architecture]
```

### Best Practices for Deep Reasoning:
1. **Adversarial Prompting**:
   - *"Analyze 3 edge cases where invalid chemical notation (e.g., `\Delta H`, unbalanced redox states) could crash the LangGraph video script parser, and specify guardrails before writing code."*
2. **Strict Thinking-Execution Separation**:
   - Use `$wf-discover` to force thorough reasoning during the planning stage. Never let an agent brainstorm and modify production code in the same unconstrained turn.

---

## 4. CLI Power Workflows

### 4.1. Fast Navigation via Skills
- Trigger standardized procedures instantly via slash commands:
  - `/$wf-discover` : Explore, analyze codebase, and produce a discovery contract.
  - `/$wf-implement` : Begin bounded implementation after Gate H1 approval.
  - `/$wf-verify` : Run independent read-only verification before merge.
  - `/$sk-solution-design` : Request expert architectural consultation.

### 4.2. Safe Experimentation with Git Worktrees
When testing speculative architectural changes (such as benchmarking Manim vs. Remotion for video rendering) without dirtying the current branch:
- Launch subagents inside isolated Git worktrees:
  ```bash
  git worktree add .claude/worktrees/spike-manim-engine -b spike-manim
  ```
- Easily merge or discard experimental changes after evaluation without leaving leftover artifacts in your primary working tree.

### 4.3. Automated Test Evidence Capture (`artifacts/evidence/`)
Never rely on an agent's conversational assurance that tests passed. Pipe actual test outputs into evidence files:
```bash
pytest tests/unit/ -v --tb=short | tee artifacts/evidence/CHG-002/unit_test_run.log
```
The raw execution log serves as verifiable proof for the `reviewer` at Gate H3.

### 4.4. Managing Durable Working Memory
For complex tasks spanning multiple days or developer sessions:
1. Maintain the active plan at: `docs/plans/active/CHG-xxx-<name>.md`.
2. Keep tasks, decisions, and discovered risks updated in this single file.
3. Upon passing Gate H3, move the file to: `docs/plans/completed/CHG-xxx-<name>.md`.

This ensures that any team member—or a fresh AI session—can immediately resume work with zero loss of institutional context.
