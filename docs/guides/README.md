# Agent Harness & AI Engineering Guides

Comprehensive guides on the Harness Layer architecture, skill definitions, 3-phase workflows, agent role boundaries, and power tips & tricks for modern CLI tools (Claude Code, OpenAI Codex CLI) paired with frontier AI reasoning models (Claude 3.7 Sonnet/Opus, OpenAI o3/o1/GPT-4o, Gemini 2.0/3.7 Flash Thinking).

---

## 📚 Guide Index

1. [**01. Harness Architecture & Core Philosophy**](01-harness-architecture-and-philosophy.md)
   - The essence of the Harness Layer: Why using the Git repository as the system of record outperforms heavy external task databases.
   - Eliminating core AI bottlenecks: Context rot, hallucinations, over-engineering, regression, and session amnesia.
   - Comparative analysis & case study: Freeform prompting vs. Harness-driven AI engineering.

2. [**02. Defining Skills & Orchestrating Workflows**](02-skills-and-workflows-definition.md)
   - Standard directory structure for skills under `.agents/skills/<skill-name>/`.
   - Skill taxonomy: Reusable capability skills (`sk-solution-design`, `sk-backend-engineering`, `sk-ai-engineering`, `sk-test-engineering`, `sk-quality-check`, `sk-release-check`) vs. orchestration workflows (`wf-discover`, `wf-implement`, `wf-verify`).
   - Closed-loop 3-phase lifecycle and human-in-the-loop control gates (H1, H2, H3).
   - Handoff contracts, the single-writer rule, and evidence-based executable proof.

3. [**03. Agent Roles & Sandbox Boundaries**](03-agent-roles-and-sandbox-boundaries.md)
   - Specialized agent profiles in `.codex/agents/`: `architect`, `backend-dev`, `ai-dev`, `reviewer`.
   - Sandbox boundary guarantees: Why `reviewer` must strictly be `read-only` to prevent the "self-grading student" anti-pattern.
   - Authority boundaries and disjoint mutable paths for safe parallel agent execution.

4. [**04. Power Tips & Tricks for CLIs and Frontier Models**](04-frontier-models-and-cli-power-tips.md)
   - Leveraging frontier reasoning models (Claude 3.7 Thinking, OpenAI o3/o1, Gemini 3.7 Flash Thinking).
   - Context window optimization & prompt caching mechanics (avoiding codebase dumps).
   - Subagents, Git worktrees for safe experimentation, deterministic test seams, and automated test evidence (`artifacts/evidence/`).
   - Durable memory management across sessions via `docs/plans/active/` and `docs/plans/completed/`.

5. [**05. Playbook: From Brainstorming & Ideation to Production Code**](05-brainstorming-and-discovery-playbook.md)
   - End-to-end playbook for turning vague ideas into bounded specifications and verifiable production code.
   - The "Clarifying Questions" pattern (`needs-input`) to prevent hallucinated business logic.
   - Classifying work shapes: Spike vs. Bounded Change vs. Architectural Change.

---

## 🎯 Core Invariants

- **Repository as System of Record**: All truth concerning architecture, documentation, source code, plans, and verification evidence resides within the Git repository.
- **Evidence over Claims**: Model claims do not prove behavior; only executable command outputs, test results, runtime logs, and verifiable artifacts establish completion.
- **Human Authority**: AI agents propose and execute within bounded scopes; human judgment governs critical transition points (H1: Architecture & Scope, H2: High-Risk Actions, H3: Release & Merge Approval).
