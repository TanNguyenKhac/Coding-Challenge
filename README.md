# 🧪 AI Chemistry Video Request Engine

> A high-reliability, cost-efficient, asynchronous backend service for generating educational chemistry video explanations using **FastAPI**, **LangGraph**, **SQLAlchemy 2.0**, and **JobQueue Concurrency Workers**.

---

## 🌟 Key Highlights

- ⚡ **Asynchronous Non-blocking API**: FastAPI endpoints provide instant responses (< 50ms) for job submissions, returning job status immediately.
- 🔄 **LangGraph Pipeline Orchestration**: Uses LangGraph `StateGraph` for visual and audio generation workflow, retry loops, and pedagogical quality gates.
- 🛡️ **100% Pydantic Structured Output (Zero Regex)**: Model calls strictly bind to Pydantic schemas via `llm.with_structured_output(VideoScript)`, eliminating fragile markdown fence / regex parsing errors.
- 🚀 **Parallel Chunk Workers & Concurrency Queue**: Decomposes scripts into scenes/chunks, processing Audio (TTS) and Slide rendering in parallel (`asyncio.gather`), throttled by `AsyncioWorkerQueue` (`MAX_CONCURRENT_JOBS`).
- 💰 **Zero-Cost Local Media Stack**: Programmatic slide rendering (Pillow 1280×720 Dark Theme), free TTS (gTTS with offline `pyttsx3` fallback), and FFmpeg assembly with per-chunk audio-visual duration synchronization.
- 🔁 **Resilience & Fault Tolerance**: Automatic retry on schema/content validation failures (max 2 retries), server restart recovery (`reset_stuck_jobs`), and independent database session management.

---

## 📋 3 Required Chemistry Concepts Supported

The engine natively generates end-to-end video explanations for the 3 core chemistry topics:
1. `How does the pH scale work?` — Acid-base logarithmic scale and $H^+$ ion concentration.
2. `Why do atoms form covalent bonds?` — Electron sharing, octet rule, and molecular stability.
3. `What is the difference between ionic and covalent bonding?` — Complete electron transfer vs. mutual electron sharing.

---

## 🛠️ Prerequisites

1. **Python**: Python 3.11+
2. **FFmpeg**: (Optional for unit tests, required for real video assembly)
   - Windows: `winget install Gyan.FFmpeg` or download from [ffmpeg.org](https://ffmpeg.org/)
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt-get install -y ffmpeg`
3. **LLM Provider** *(Choose one)*:
   - **Option A (Primary / Free Local)**: OpenAI-compatible endpoint (e.g. Codex, Ollama, vLLM, LMStudio).
   - **Option B (Fallback / Cloud)**: Anthropic API Key (`claude-haiku-4-5-20251001`).

---

## 🚀 Quick Start & Installation

### 1. Clone & Setup Environment

```bash
# Clone the repository
git clone https://github.com/your-org/chemistry-video-engine.git
cd chemistry-video-engine

# Create and activate virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration (`.env`)

Copy `.env.example` to `.env` and set your preferred configuration:

```bash
cp .env.example .env
```

**Sample `.env` options:**

```dotenv
# Option A: Local Codex / OpenAI-compatible endpoint (Free / Local)
CODEX_API_BASE=http://localhost:11434/v1
CODEX_MODEL=codex-mini-latest
CODEX_API_KEY=not-needed

# Option B: Anthropic Claude (Fallback)
# ANTHROPIC_API_KEY=sk-ant-api03-...

# Database & Concurrency
DATABASE_URL=sqlite+aiosqlite:///./chemistry.db
ARTIFACTS_DIR=./artifacts/videos
MAX_RETRIES=2
MAX_CONCURRENT_JOBS=2
```

### 3. Run the Server

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- Swagger Interactive UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Redoc Documentation: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 📡 API Reference & Usage Examples

### 1. Request Video Generation
`POST /api/v1/jobs`

```bash
curl -X POST http://127.0.0.1:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "concept": "How does the pH scale work?",
    "config": {
      "target_duration_sec": 60,
      "target_audience": "high_school",
      "aspect_ratio": "16:9",
      "language": "vi"
    }
  }'
```

**Response (`201 Created`):**
```json
{
  "job_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "concept": "How does the pH scale work?",
  "config": {
    "target_duration_sec": 60,
    "target_audience": "high_school",
    "aspect_ratio": "16:9",
    "resolution": [1280, 720],
    "language": "vi",
    "voice_gender": "neutral"
  },
  "status": "pending",
  "created_at": "2026-09-13T10:00:00Z",
  "updated_at": "2026-09-13T10:00:00Z",
  "artifact_url": null,
  "error_reason": null
}
```

---

### 2. List All Requested Jobs
`GET /api/v1/jobs`

```bash
curl -X GET http://127.0.0.1:8000/api/v1/jobs
```

---

### 3. Get Job Details & Status
`GET /api/v1/jobs/{job_id}`

```bash
curl -X GET http://127.0.0.1:8000/api/v1/jobs/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d
```

**Response (`200 OK - When Complete`):**
```json
{
  "job_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "concept": "How does the pH scale work?",
  "config": { ... },
  "status": "complete",
  "created_at": "2026-09-13T10:00:00Z",
  "updated_at": "2026-09-13T10:00:45Z",
  "artifact_url": "/artifacts/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d.mp4",
  "error_reason": null
}
```

---

### 4. Download Video Artifact
`GET /api/v1/jobs/{job_id}/artifact`

```bash
curl -O -J http://127.0.0.1:8000/api/v1/jobs/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d/artifact
```

---

## 🧪 Testing & Verification

### 1. Run Unit Tests (Fast, Zero Dependencies, Zero API Cost)

```bash
pytest tests/ -v --tb=short
```

*Runs with in-memory SQLite, Mock LLM with structured output, and MockAssembler. Completes in < 5 seconds.*

### 2. Run End-to-End Smoke Test (Repeatability Proof)

Executes 2 consecutive runs on all 3 required chemistry concepts against the running server:

```bash
python scripts/smoke_test.py
```

### 3. Generate Committed Sample Videos

```bash
python scripts/generate_samples.py
```

Generated sample MP4s are placed in `artifacts/samples/`:
- `artifacts/samples/job-ph-scale.mp4`
- `artifacts/samples/job-covalent-bonds.mp4`
- `artifacts/samples/job-ionic-vs-covalent.mp4`

---

## 📚 Agent Harness & Engineering Guides

This repository implements a production-grade **Agent Harness Layer** designed to structure, constrain, and supercharge AI-assisted software engineering (using tools like **Claude Code CLI**, **OpenAI Codex**, and frontier reasoning models such as Claude 3.7 Thinking, OpenAI o3/o1, and Gemini 3.7 Flash Thinking).

Comprehensive documentation and playbooks are available in [`docs/guides/`](docs/guides/README.md):

- [**01. Harness Architecture & Philosophy**](docs/guides/01-harness-architecture-and-philosophy.md): Why using Git as the single system of record eliminates context rot, hallucinations, and regression bugs. Includes direct comparative analysis against freeform prompting.
- [**02. Defining Skills & Orchestrating Workflows**](docs/guides/02-skills-and-workflows-definition.md): Anatomy of capability skills (`sk-*`) and 3-phase workflows (`wf-discover`, `wf-implement`, `wf-verify`) guarded by human-in-the-loop gates (**H1** Design, **H2** High-Risk, **H3** Release).
- [**03. Agent Roles & Sandbox Boundaries**](docs/guides/03-agent-roles-and-sandbox-boundaries.md): Specialized profiles (`architect`, `backend-dev`, `ai-dev`, `reviewer`), why the reviewer must strictly be `read-only`, and single-writer disjoint path safety.
- [**04. CLI Power Tips & Frontier Models**](docs/guides/04-frontier-models-and-cli-power-tips.md): Extended reasoning model alignment, context window & prompt caching optimization, isolated Git worktrees, and automated test evidence capture in `artifacts/evidence/`.
- [**05. Discovery & Brainstorming Playbook**](docs/guides/05-brainstorming-and-discovery-playbook.md): Step-by-step playbook to transform vague product ideas into structured discovery contracts and verifiable code without losing control.

---

## 📂 Repository Structure

```
├── .agents/skills/              # Canonical repository skills & workflow definitions
│   ├── wf-discover/             # Discovery workflow (delegates to architect)
│   ├── wf-implement/            # Implementation workflow (parallel safe dev packages)
│   ├── wf-verify/               # Independent verification workflow (read-only reviewer)
│   └── sk-*/                    # Capability skills (backend, AI, testing, quality, release)
├── .codex/agents/               # Specialized agent sandbox profiles (architect, devs, reviewer)
├── app/
│   ├── main.py                  # FastAPI application & lifespan worker management
│   ├── config.py                # Environment configuration (pydantic-settings)
│   ├── database.py              # SQLAlchemy 2.0 async engine & session factory
│   ├── llm_factory.py           # Provider selector (Codex / Anthropic / Mock)
│   ├── api/v1/jobs.py           # 4 REST API route handlers
│   ├── models/job.py            # SQLAlchemy Job ORM model & JobStatus enum
│   ├── schemas/
│   │   ├── job.py               # VideoConfig, JobCreate, JobResponse
│   │   └── script.py            # ScriptChunk, VideoScript (Structured Output)
│   ├── repositories/
│   │   └── job_repository.py    # Sole database reader/writer
│   ├── services/
│   │   ├── queue.py             # JobQueue ABC & AsyncioWorkerQueue
│   │   └── job_service.py       # Pipeline runner with isolated session
│   └── pipeline/
│       ├── state.py             # VideoGenerationState TypedDict
│       ├── graph.py             # LangGraph StateGraph topology
│       ├── assembler.py         # VideoAssembler, FFmpegAssembler, MockAssembler
│       └── nodes/
│           ├── script_node.py   # LLM Structured Output node
│           ├── validator_node.py# Pedagogical checks & retry routing
│           ├── audio_node.py    # Parallel chunk TTS workers
│           ├── slides_node.py   # Parallel chunk Pillow visual workers
│           └── assembler_node.py# FFmpeg duration sync & MP4 assembly
├── docs/
│   ├── guides/                  # Comprehensive Harness & AI Engineering guides (01-05)
│   ├── biz.md                   # Product business requirements
│   ├── specs/                   # Detailed functional specifications (SPEC-01 to SPEC-05)
│   ├── plans/active/            # Active execution plan (CHG-002)
│   ├── workflows/               # Handoff contracts & schema definitions
│   └── ARCHITECTURE.md          # Architectural blueprints & cost analysis
├── scripts/
│   ├── smoke_test.py            # Automated 2-run repeatability test
│   └── generate_samples.py      # Pre-generate committed sample MP4s
├── artifacts/
│   ├── handoffs/                # Structured inter-phase handoff YAML contracts
│   ├── evidence/                # Verified test & execution logs
│   ├── videos/                  # Runtime video output store
│   └── samples/                 # 3 committed reference sample videos
└── tests/
    ├── conftest.py              # In-memory DB, Mock LLM, Mock Assembler fixtures
    ├── test_api.py              # API endpoint & repository tests
    ├── test_pipeline.py         # LangGraph node & graph tests
    └── test_queue.py            # Worker pool concurrency tests
```

---

## 📄 License & Attribution

Designed and engineered for the **Agentic Backend Challenge — AI Chemistry Video Request Service**.
