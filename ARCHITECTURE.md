# 🏛️ Architecture & System Blueprint: Chemistry Video Engine

This document outlines the technical architecture, data boundaries, concurrency model, pipeline topology, reliability mechanisms, and production cost economics for the **AI Chemistry Video Request Engine**.

---

## 1. Architectural Principles & System Layers

The system follows **Clean Architecture** principles with strict boundary separation between HTTP ingestion, concurrency control, pipeline orchestration, persistence, and media generation.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             HTTP Ingestion Layer                            │
│           FastAPI Router: POST /jobs | GET /jobs | GET /artifact            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Non-blocking Enqueue (< 50ms)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Queue & Worker Pool Layer                          │
│     JobQueue Abstraction ──► AsyncioWorkerQueue (concurrency limiter)       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Pop job_id (Independent DB Session)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Pipeline Orchestration Layer                        │
│                     LangGraph StateGraph Execution Flow                     │
│   [generate_script] ─► [validate_script] ─► [audio_node & slides_node]      │
│           ▲ (Retry Loop)        │                      │ (Fan-out / Fan-in) │
│           └─────────────────────┘                      ▼                    │
│                                                 [assemble_video]            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            ▼                                                     ▼
┌──────────────────────────────┐              ┌───────────────────────────────┐
│     Persistence Boundary     │              │    Media & Provider Layer     │
│ SQLAlchemy 2.0 Async Session │              │ LLM Factory (Codex/Anthropic) │
│ JobRepository (Sole Writer)  │              │ gTTS / pyttsx3 Audio Workers  │
│ SQLite File Storage (Dev)    │              │ Pillow Slides / FFmpeg Assembl│
└──────────────────────────────┘              └───────────────────────────────┘
```

---

## 2. Job Lifecycle & State Transitions

Every video request is represented by a unique UUID `job_id` and transitions through a deterministic state machine:

```
                  Client POST /api/v1/jobs
                             │
                             ▼
                    ┌─────────────────┐
                    │     PENDING     │  (Recorded in DB, pushed to JobQueue)
                    └────────┬────────┘
                             │ Worker picks up job
                             ▼
                    ┌─────────────────┐
                    │   GENERATING    │  (LangGraph Pipeline Running)
                    └────────┬────────┘
                             │
            ┌────────────────┴────────────────┐
            │                                 │
     Pipeline Success                  Pipeline Failure
 (Video rendered & synced)         (Max retries / exception)
            │                                 │
            ▼                                 ▼
   ┌─────────────────┐               ┌─────────────────┐
   │    COMPLETE     │               │     FAILED      │
   │  (artifact_url  │               │  (error_reason  │
   │    available)   │               │   populated)    │
   └─────────────────┘               └─────────────────┘
```

### Server Restart & Stuck Job Recovery
- **Failure Scenario**: The application is restarted or crashes while jobs are in `generating` state.
- **Recovery Policy**: During FastAPI lifespan startup, `JobRepository.reset_stuck_jobs()` queries all jobs with status `generating` and safely transitions them to `failed` with `error_reason="server_restart"`, preventing zombie states.

---

## 3. Queue & Concurrency Worker Architecture

To prevent CPU/RAM exhaustion during video rendering, the engine isolates Web API requests from worker execution via a **Queue Abstraction Layer**:

```
                  POST /jobs (Web API)
                           │
                           │ await job_queue.enqueue(job_id)
                           ▼
                  ┌─────────────────┐
                  │    JobQueue     │ (Abstract Interface)
                  └────────┬────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼ (In-Process Dev)          ▼ (Distributed Production)
  ┌───────────────────────┐    ┌──────────────────────────┐
  │   AsyncioWorkerQueue  │    │  RedisBrokerQueue (ARQ)  │
  │ - asyncio.Queue[str]  │    │ - Distributed Celery/RQ  │
  │ - Concurrency: 2      │    │ - GPU Render Nodes       │
  └──────────┬────────────┘    └──────────────────────────┘
             │
             ├──► Worker-0: run_pipeline(job_1) [Active]
             ├──► Worker-1: run_pipeline(job_2) [Active]
             └──► [Job 3, Job 4 queued in memory]
```

### Key Engineering Features:
- **Backpressure & Concurrency Limiting**: `MAX_CONCURRENT_JOBS` limits the number of FFmpeg/TTS renders executing simultaneously.
- **Independent Session Management**: Each worker thread/coroutine creates its own DB session via `async with async_session_factory() as session:`, preventing session collision with the HTTP event loop.
- **Zero External Dependency in Dev**: Runs out-of-the-box without requiring Redis or RabbitMQ.

---

## 4. LangGraph StateGraph & Chunking Pipeline

The video generation workflow is structured as a directed graph in **LangGraph**:

```
                       START
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               Node 1: generate_script (ai-dev)                  │
│  - Invokes LLM via with_structured_output(VideoScript)          │
│  - Produces N ScriptChunks (0-indexed, pedagogical breakdown)   │
│  - 100% Type-Safe: NO REGEX PARSING                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               Node 2: validate_script (quality-gate)            │
│  - Verifies: len(chunks) >= 3, non-empty headings & narrations  │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────────────┐
        │ [PASS]                                  │ [FAIL]
        │                                         ├─ retry_count < 2 ──► (Retry generate_script)
        │                                         └─ retry_count >= 2 ─► [mark_failed] ──► END
        ▼
┌─────────────────────────────────────────────────────────────────┐
│          Parallel Chunk Execution: Nodes 3 & 4 (Fan-Out)        │
│                                                                 │
│    generate_audio (TTS)             generate_slides (Pillow)    │
│    ├── audio_chunk_0.mp3            ├── slide_chunk_0.png       │
│    ├── audio_chunk_1.mp3   (async)  ├── slide_chunk_1.png       │
│    └── audio_chunk_2.mp3            └── slide_chunk_2.png       │
└────────────────────────┬────────────────────────────────────────┘
                         │ (Fan-In Barrier Sync)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               Node 5: assemble_video (FFmpeg)                   │
│  - Measures duration of audio_chunk_i.mp3                       │
│  - Generates clip_i.mp4 with slide display duration = audio_len │
│  - Concat demuxer concatenates clips into artifacts/{job_id}.mp4│
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
                 [mark_complete] ──► END
```

---

## 5. Persistence Boundary

The database boundary is strictly governed by `JobRepository`:
- **Single Source of Truth**: The database (`chemistry.db`) records durable metadata: `job_id`, `concept`, `config` (JSON), `status`, `error_reason`, `artifact_path`, `retry_count`, `created_at`, `updated_at`.
- **Sole Writer Pattern**: LangGraph nodes do not directly execute raw SQL. All status transitions and metadata updates go through `JobRepository.update_status()`.

---

## 6. Provider Interfaces & STEM Extensibility

### 6.1 LLM Provider Interface (`BaseChatModel`)
The pipeline consumes standard LangChain `BaseChatModel` interfaces:
- **Local / Dev Primary**: `ChatOpenAI` configured with `CODEX_API_BASE` (local endpoint, zero token cost).
- **Cloud Fallback**: `ChatAnthropic` (`claude-haiku-4-5-20251001`) when `ANTHROPIC_API_KEY` is provided.
- **Testing**: `FakeListChatModel` providing deterministic `VideoScript` outputs.

### 6.2 Video Assembler Interface (`VideoAssembler`)
```python
class VideoAssembler(ABC):
    @abstractmethod
    async def assemble(self, job_id: str, script: VideoScript,
                       audio_paths: list[str], slide_paths: list[str],
                       output_dir: str) -> str: ...
```
- `FFmpegAssembler`: Production assembler using FFmpeg filter complex / concat demuxer.
- `MockAssembler`: Fast stub writer for CI test environments.

### 6.3 Extensibility to Other STEM Topics
Adding support for Physics, Biology, or Mathematics requires **zero changes** to the graph topology or API contracts:
1. Update prompt templates in `script_node.py` or pass `subject: str` via `VideoConfig`.
2. Extend visual formula rendering styles in `slides_node.py`.

---

## 7. Cost Breakdown & Production Economics

The table below details the cost breakdown for generating a standard 60-second chemistry explanation video:

| Component | Technology | Local Dev Cost | Production Cloud Cost (Estimated) | Cost Optimization Strategy |
|---|---|---|---|---|
| **Script Generation** | Claude Haiku 4.5 / Codex Mini | **$0.00** (Codex) | ~$0.0015 (1,200 input tokens, 800 output tokens) | Pydantic Structured Output eliminates retry token waste |
| **Audio Narration (TTS)** | gTTS (with pyttsx3 fallback) | **$0.00** (Free) | $0.00 (gTTS) or ~$0.002 (AWS Polly / ElevenLabs) | Chunk-level caching and pyttsx3 offline fallback |
| **Slide Visuals** | Pillow 1280×720 (Dark Theme) | **$0.00** (Local CPU) | $0.00 (Local CPU rendering) | Programmatic SVG/PNG rendering avoids costly GenAI image APIs |
| **Video Assembly** | FFmpeg (H.264 / AAC Concat) | **$0.00** (Local CPU) | ~$0.0005 (Server compute time ~2.5s) | Direct stream copy concatenation |
| **Database & Queue** | SQLite + AsyncioWorkerQueue | **$0.00** | ~$0.0001 (Shared Postgres + Redis) | Minimal I/O footprint |
| **TOTAL PER VIDEO** | **Full Pipeline** | **$0.00** | **~$0.0021 (~$2.10 per 1,000 videos)** | **Maximum cost efficiency with high reliability** |

---

## 8. Reliability Under Non-Determinism

| Risk / Failure Mode | Root Cause | Architectural Mitigation |
|---|---|---|
| **Malformed JSON / Markdown Fences** | LLM non-determinism in raw text mode | **100% Pydantic Structured Output** (`with_structured_output`), zero regex. |
| **Pedagogical Incompleteness** | LLM outputs too few sections or shallow notes | **Validator Quality Gate** checks `len(chunks) >= 3` and non-empty content with **Auto-Retry (max 2)**. |
| **Audio-Visual Desync** | Slide timing fixed while audio duration varies | **Dynamic Duration Sync**: FFmpeg measures exact audio chunk duration and pins slide duration to it. |
| **Network Loss during TTS** | External TTS service failure / rate-limit | **Automatic Offline Fallback** from gTTS to local `pyttsx3`. |
| **Server Crash during Generation** | Process killed or container restarted | **Startup Event Hook** (`reset_stuck_jobs`) cleans orphaned generating states. |
| **Concurrent Render Overload** | Too many simultaneous video requests | **AsyncioWorkerQueue** bounds concurrency (`MAX_CONCURRENT_JOBS = 2`). |
