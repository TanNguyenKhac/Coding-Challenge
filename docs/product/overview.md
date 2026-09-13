# Chemistry Video Request Service

## Product

AI-native backend service for educational chemistry content. A learner submits
a chemistry concept query, the backend processes it as an asynchronous
video-generation job, and the learner can check status and retrieve the
completed video when ready.

Latency is not a major issue. The video does not need to generate instantly.
The backend must handle the waiting state clearly and expose it through the API.

## Source Specification

[Agentic_Backend_Challenge_AI_Chemistry_Video_Request_Service.md](../Agentic_Backend_Challenge_AI_Chemistry_Video_Request_Service.md)

## Required Queries

The prototype must support these three learner queries end-to-end:

1. How does the pH scale work?
2. Why do atoms form covalent bonds?
3. What is the difference between ionic and covalent bonding?

These three are the required scope. Design the backend so other STEM topics
can be added later.

## Technical Constraints

- FastAPI backend (no frontend).
- API endpoint where a client can request a chemistry concept explanation video.
- Asynchronous video-generation flow.
- List requested videos or jobs with visible status.
- Retrieve or open a completed video explanation artifact.
- Visual content and audio for the explanation.
- Clear backend boundary for job state, generation logic, persistence, and
  artifacts.

## Persistence and Simulation Policy

- In-memory persistence acceptable if the boundary is clean.
- Simple local file/artifact store acceptable.
- Mocked or partly simulated generation acceptable if the service design makes
  it clear where real AI/video-generation providers would be plugged in.

## Cost Constraint

"Best visual explanation at cheapest reasonable cost." Both cost-efficiency and
visual quality are success metrics. Solutions should explain:

- what was optimized for;
- approximate cost per generated artifact or what it would cost in production;
- how the backend avoids flaky generation from non-deterministic outputs.

## Reliability Requirements

LLMs and generative media tools are non-deterministic. The pipeline must:

- treat non-determinism as an engineering problem;
- validate generated output before it reaches the learner;
- define understandable failure states instead of failing silently or halfway;
- apply retries, fallbacks, guardrails, or quality gates where appropriate;
- produce consistent results across repeated runs of the same concept.

## Evaluation Dimensions

| Dimension | What evaluators look for |
|---|---|
| Product judgement | Translate requirement into a sensible backend slice; decide what to build, fake, simplify, or leave out |
| Architecture | Practical backend architecture, clean API, job lifecycle, async state reasoning, cost tradeoffs |
| Reliability | Consistent output across repeated runs, validation gates, retries, fallbacks, guardrails |
| AI-agent workflow | Clear implementation plans, agent steering, coherent steps, behavior verification |
| Quality | Testing, error handling, observability, API clarity, production-evolvable boundaries |
| Video quality | Visually pleasing, educationally clear, cost-conscious |

## Deliverables

- FastAPI backend codebase.
- `README.md` with setup, run, API, and test instructions.
- Architecture note: job lifecycle, persistence/artifact boundary,
  AI/video-generation boundary.
- Demo video or API walkthrough showcasing the three required chemistry
  concepts.
- Three best generated videos committed into the repo, along with the input
  learner query that produced each video.
- Screen and face recording of work session.

## Timebox

90–120 minutes. Completion is not the end goal. Evaluators care about planning,
architectural decision-making, and ability to guide AI coding agents
effectively. Do not try to maximize surface area.
