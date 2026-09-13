# CHG-002 Chemistry Video MVP — LangGraph + SQLAlchemy + FastAPI + JobQueue

## Mục tiêu

Backend FastAPI điều phối video generation qua LangGraph StateGraph, lưu job state bằng SQLAlchemy 2.0 (SQLite), quản lý worker pool qua JobQueue abstraction, sinh kịch bản với Pydantic Structured Output (zero regex), render song song các chunks (scenes), và tạo video MP4 hoàn chỉnh kèm audio narration.

## Context

- Change ID: CHG-002
- Discovery handoff: artifacts/handoffs/CHG-002-discovery.yaml
- Base revision: 2cf89b0e20c3d8bfd2e7ed884770fb24b4643c72
- Timebox: 120 phút
- Mode: architectural
- Thay thế: CHG-001 (custom orchestrator + in-memory dict)

## Công nghệ đã quyết định

| Layer | Technology | Lý do |
|---|---|---|
| Web framework | FastAPI + uvicorn | Bắt buộc (EVD-001) |
| Queue & Worker Pool | `JobQueue` (In-Process `AsyncioWorkerQueue` concurrency-limited) | Tách biệt API & Worker; kiểm soát tải (EVD-013, EVD-019) |
| Pipeline orchestration | LangGraph StateGraph | Graph topology, retry loop (EVD-011) |
| LLM Structured Output | LangChain `with_structured_output(VideoScript)` | 100% type-safe, loại bỏ hoàn toàn regex parse JSON (EVD-018) |
| LLM (primary) | LangChain ChatOpenAI → Codex endpoint | Provider inject; zero external cost trong dev |
| LLM (fallback) | LangChain ChatAnthropic (Haiku) | Khi `CODEX_API_BASE` không set |
| Persistence | SQLAlchemy 2.0 async + SQLite | Independent session per worker task (EVD-012, EVD-019) |
| TTS | gTTS + pyttsx3 fallback | Free/offline, song song per chunk |
| Slides | Pillow | Local, zero cost, song song per chunk |
| Video assembly | ffmpeg-python | Local, sync slide display với audio duration per chunk |

## Cấu trúc thư mục mục tiêu

```
app/
  main.py                   # FastAPI app, lifespan (worker pool start/stop), static mount
  config.py                 # Settings (pydantic-settings), env vars
  api/
    v1/
      jobs.py               # 4 route handlers (POST, GET, GET /{id}, GET /{id}/artifact)
  models/
    job.py                  # SQLAlchemy Job ORM model + JobStatus enum
  schemas/
    job.py                  # Pydantic models: VideoConfig, JobCreate, JobResponse
    script.py               # Pydantic models: ScriptChunk, VideoScript (Structured Output)
  repositories/
    job_repository.py       # JobRepository — sole DB writer
  database.py               # async engine, session factory, create_tables
  services/
    queue.py                # JobQueue ABC + AsyncioWorkerQueue (concurrency limiter)
    job_service.py          # run_pipeline(job_id) với async_session_factory
  pipeline/
    state.py                # VideoGenerationState TypedDict
    graph.py                # LangGraph StateGraph definition
    assembler.py            # VideoAssembler ABC + FFmpegAssembler + MockAssembler
    nodes/
      script_node.py        # generate_script (LLM with_structured_output)
      validator_node.py     # validate_script (business validation & retry routing)
      audio_node.py         # generate_audio (parallel chunk TTS workers)
      slides_node.py        # generate_slides (parallel chunk Pillow workers)
      assembler_node.py     # assemble_video (FFmpeg sync & concat)
  llm_factory.py            # build_llm() factory (Codex / Anthropic / Mock)
tests/
  conftest.py               # fixtures: test DB, mock LLM, mock assembler, test client
  test_api.py               # endpoint tests, config validation
  test_pipeline.py          # node-level, graph topology, structured output, retry tests
  test_queue.py             # worker queue concurrency tests
scripts/
  smoke_test.py             # end-to-end 3 required queries (2 consecutive runs)
  generate_samples.py       # pre-generate sample videos committed to artifacts
artifacts/
  videos/                   # generated runtime videos
  samples/                  # 3 committed sample MP4s
requirements.txt
.env.example
README.md
ARCHITECTURE.md
```

## LangGraph Graph & Chunking Design

```
START
  │
  ▼
generate_script (LLM Structured Output: VideoScript)
  │
  ▼
validate_script (Business check: >= 3 chunks, non-empty fields)
  ├─ PASS ──────────────────────────────────────────────────┐
  ├─ FAIL + retry_count < 2 → increment retry_count ────────┘ (quay lại generate_script)
  └─ FAIL + retry_count >= 2 ──────────────────────────────► mark_failed → END
                                                                │
generate_audio (Fan-out: N chunks TTS song song) ───────────► generate_slides
                                                                │
generate_slides (Fan-out: N chunks Pillow song song) ───────► assemble_video
                                                                │
assemble_video (FFmpeg: sync slide duration theo audio) ───► mark_complete → END
```

## Schemas & State Definition

### 1. VideoConfig & JobCreate (`app/schemas/job.py`)
```python
class VideoConfig(BaseModel):
    target_duration_sec: int = Field(default=60, description="Thời lượng mục tiêu")
    target_audience: str = Field(default="high_school", description="Đối tượng: high_school, university, beginner")
    aspect_ratio: str = Field(default="16:9", description="Tỉ lệ khung hình: 16:9, 9:16")
    resolution: tuple[int, int] = Field(default=(1280, 720), description="Độ phân giải (width, height)")
    language: str = Field(default="vi", description="Ngôn ngữ thuyết minh và phụ đề")
    voice_gender: str = Field(default="neutral", description="Giọng đọc TTS")

class JobCreate(BaseModel):
    concept: str = Field(..., description="Khái niệm hóa học cần giải thích")
    config: Optional[VideoConfig] = Field(default_factory=VideoConfig, description="Cấu hình tùy chọn cho video")

class JobResponse(BaseModel):
    job_id: str
    concept: str
    config: VideoConfig
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    artifact_url: Optional[str] = None
    error_reason: Optional[str] = None
```

### 2. Structured Output Script (`app/schemas/script.py`)
```python
class ScriptChunk(BaseModel):
    chunk_id: int = Field(description="Index của scene/section (0-indexed)")
    heading: str = Field(description="Tiêu đề phân đoạn bài giảng")
    narration: str = Field(description="Lời thuyết minh chi tiết cho TTS")
    visual_notes: str = Field(description="Mô tả công thức/hình ảnh hiển thị trên slide")
    duration_hint_sec: Optional[int] = Field(default=None, description="Thời lượng ước tính")

class VideoScript(BaseModel):
    title: str = Field(description="Tiêu đề video bài giảng")
    summary: str = Field(description="Tóm tắt ngắn gọn bài học")
    chunks: list[ScriptChunk] = Field(description="Danh sách các phân đoạn (tối thiểu 3 chunks)")
```

### 3. VideoGenerationState (`app/pipeline/state.py`)
```python
class VideoGenerationState(TypedDict):
    job_id: str
    concept: str
    config: VideoConfig
    script: NotRequired[VideoScript]
    audio_paths: NotRequired[list[str]]    # Ordered audio paths per chunk
    slide_paths: NotRequired[list[str]]    # Ordered slide PNG paths per chunk
    artifact_path: NotRequired[str]       # Final MP4 path
    retry_count: int                      # Mặc định 0
    error_reason: NotRequired[str]
    status: str
```

## Job Lifecycle & Queue Architecture

```
Client POST /api/v1/jobs {concept, config?}
  │
  ├─► JobRepository.create(status="pending", config=...)  [Fast Response]
  ├─► await job_queue.enqueue(job_id)
  └─► Trả về HTTP 201 {job_id, status: "pending"}

AsyncioWorkerPool (background lifespan tasks)
  │
  ├─► Pop job_id từ asyncio.Queue (concurrency <= MAX_CONCURRENT_JOBS)
  ├─► async with async_session_factory() as session:
  │     repo = JobRepository(session)
  │     await repo.update_status(generating)
  │     final_state = await video_graph.ainvoke(state)
  │     await repo.update_status(complete, artifact_path=...) hoặc failed
```

## Interfaces đóng băng (không thay đổi giữa WP)

### API Contract
```
POST   /api/v1/jobs          body: {concept: str, config?: VideoConfig}
                             resp: 201 {job_id, concept, config, status, created_at}

GET    /api/v1/jobs          resp: 200 [{job_id, concept, config, status, created_at, updated_at}]

GET    /api/v1/jobs/{id}     resp: 200 {job_id, concept, config, status, created_at,
                                         updated_at, artifact_url, error_reason}
                                    404 {detail: "Job not found"}

GET    /api/v1/jobs/{id}/artifact
                             resp: 200 video/mp4 (FileResponse)
                                    400 {detail: "Job not complete"} | 404
```

### JobRepository interface
```python
class JobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, concept: str, config: dict | None = None) -> Job: ...
    async def get(self, job_id: str) -> Job | None: ...
    async def list_all(self) -> list[Job]: ...
    async def update_status(self, job_id: str, status: JobStatus,
                            artifact_path: str | None = None,
                            error_reason: str | None = None,
                            retry_count: int | None = None) -> None: ...
    async def reset_stuck_jobs(self) -> None: ...
```

### VideoAssembler interface
```python
class VideoAssembler(ABC):
    @abstractmethod
    async def assemble(self, job_id: str, script: VideoScript,
                       audio_paths: list[str],
                       slide_paths: list[str]) -> str:  # path to MP4
        pass
```

---

## Work Packages

---

### WP-01 — Project scaffold, config, SQLAlchemy models, Pydantic schemas, LLM Factory

**Thứ tự:** 1  
**Owner:** backend-dev  
**Mục tiêu:** Cấu trúc thư mục, dependencies, SQLAlchemy Job model (có config JSON), Pydantic schemas (`VideoConfig`, `JobCreate`, `JobResponse`, `ScriptChunk`, `VideoScript`), config settings, database session factory, LLM factory.

**Paths:**
- app/__init__.py
- app/config.py
- app/database.py
- app/models/job.py
- app/schemas/job.py
- app/schemas/script.py
- app/llm_factory.py
- requirements.txt
- .env.example

**Config (`app/config.py`):**
- `DATABASE_URL`: default `sqlite+aiosqlite:///./chemistry.db`
- `ARTIFACTS_DIR`: default `./artifacts/videos`
- `CODEX_API_BASE`: optional (default `None`)
- `CODEX_MODEL`: default `codex-mini-latest`
- `CODEX_API_KEY`: optional
- `ANTHROPIC_API_KEY`: fallback
- `MAX_RETRIES`: default `2`
- `MAX_CONCURRENT_JOBS`: default `2`

**Lệnh kiểm tra:**
```bash
python -c "from app.models.job import Job, JobStatus; from app.schemas.job import JobCreate, JobResponse; from app.schemas.script import VideoScript; print('ok')"
python -c "import asyncio; from app.database import create_tables; asyncio.run(create_tables()); print('DB created')"
python -c "from app.llm_factory import build_llm; print('llm_factory importable')"
```

---

### WP-02 — JobRepository + session context manager + startup reset logic

**Thứ tự:** 2  
**Owner:** backend-dev  
**Mục tiêu:** `JobRepository` hỗ trợ session độc lập, method `reset_stuck_jobs()` đổi "generating" thành "failed" ("server_restart").

**Paths:**
- app/repositories/job_repository.py
- app/main.py (startup/lifespan stub)

**Lệnh kiểm tra:**
```bash
pytest tests/test_api.py::TestJobRepository -v
```

---

### WP-03 — LangGraph state (VideoGenerationState) + graph topology + node stubs

**Thứ tự:** 3  
**Owner:** backend-dev / ai-dev  
**Mục tiêu:** `VideoGenerationState` hoàn chỉnh, graph topology chuẩn với conditional routing cho retry loop, tất cả nodes là stubs.

**Paths:**
- app/pipeline/state.py
- app/pipeline/graph.py
- app/pipeline/nodes/__init__.py
- app/pipeline/nodes/script_node.py (stub)
- app/pipeline/nodes/validator_node.py (stub)
- app/pipeline/nodes/audio_node.py (stub)
- app/pipeline/nodes/slides_node.py (stub)
- app/pipeline/nodes/assembler_node.py (stub)

**Lệnh kiểm tra:**
```bash
pytest tests/test_pipeline.py::TestGraphTopology -v
```

---

### WP-04 — LangGraph nodes: script_node (Structured Output) + validator_node

**Thứ tự:** 4  
**Owner:** ai-dev  
**Mục tiêu:** `script_node` sử dụng `llm.with_structured_output(VideoScript)` — 100% không dùng regex; `validator_node` kiểm tra nghiệp vụ (len(chunks) >= 3, non-empty fields) và kích hoạt retry.

**Implementation script_node sketch:**
```python
async def script_node(state: VideoGenerationState, llm: BaseChatModel) -> VideoGenerationState:
    structured_llm = llm.with_structured_output(VideoScript)
    prompt = SCRIPT_PROMPT_TEMPLATE.format(
        concept=state["concept"],
        duration=state["config"].target_duration_sec,
        audience=state["config"].target_audience
    )
    result = await structured_llm.ainvoke(prompt)
    state["script"] = result
    return state
```

**Lệnh kiểm tra:**
```bash
pytest tests/test_pipeline.py::TestScriptNode tests/test_pipeline.py::TestValidatorNode -v
```

---

### WP-05 — LangGraph nodes: audio_node & slides_node (Parallel Chunk Workers) + assembler_node (FFmpeg Sync)

**Thứ tự:** 5  
**Owner:** ai-dev  
**Mục tiêu:**
- `audio_node`: Xử lý song song $N$ chunks qua `asyncio.gather` (gTTS với fallback pyttsx3) → `audio_paths`.
- `slides_node`: Render song song $N$ slides 1280×720 (Pillow) tương ứng từng chunk → `slide_paths`.
- `assembler_node`: Gọi `VideoAssembler.assemble()`.
  - `FFmpegAssembler`: Lấy duration audio per chunk, render video clip khớp thời lượng, ghép thành final MP4.
  - `MockAssembler`: Tạo stub MP4 hợp lệ phục vụ unit tests không cần FFmpeg binary.

**Lệnh kiểm tra:**
```bash
pytest tests/test_pipeline.py::TestVideoNodes -v
```

---

### WP-06 — JobQueue abstraction + AsyncioWorkerQueue + FastAPI endpoints + static mount

**Thứ tự:** 6  
**Owner:** backend-dev  
**Mục tiêu:** `JobQueue` & `AsyncioWorkerQueue` quản lý worker pool; `JobService.run_pipeline()` khởi tạo session độc lập; 4 API endpoints và static file mount.

**Paths:**
- app/services/queue.py
- app/services/job_service.py
- app/api/v1/jobs.py
- app/main.py

**Lệnh kiểm tra:**
```bash
pytest tests/test_api.py tests/test_queue.py -v
```

---

### WP-07 — Unit tests suite hoàn chỉnh

**Thứ tự:** 7  
**Owner:** backend-dev  
**Mục tiêu:** Tất cả test cases pass độc lập (Mock LLM, Mock Assembler, In-Memory DB, Asyncio Worker Queue).

**Paths:**
- tests/conftest.py
- tests/test_api.py
- tests/test_pipeline.py
- tests/test_queue.py

**Lệnh kiểm tra:**
```bash
pytest tests/ -v --tb=short
```

---

### WP-08 — Smoke test + pre-generate 3 sample videos

**Thứ tự:** 8  
**Owner:** ai-dev  
**Mục tiêu:** Smoke test 3 required concepts chạy thành công 2 lần liên tiếp; 3 sample MP4 được sinh và committed vào `artifacts/samples/`.

**Lệnh kiểm tra:**
```bash
CODEX_API_BASE=http://localhost:11434/v1 python scripts/smoke_test.py
ffprobe artifacts/samples/*.mp4
```

---

### WP-09 — README.md + ARCHITECTURE.md

**Thứ tự:** 9  
**Owner:** backend-dev  
**Mục tiêu:** Tài liệu hoàn chỉnh mô tả kiến trúc (JobQueue, LangGraph, Chunk Workers, Structured Output, DB Session lifecycle) và cost breakdown table.

---

## Verification Contract

1. `pytest tests/ -v` (Unit tests không cần internet / API key / external queue).
2. `CODEX_API_BASE=http://localhost:11434/v1 python scripts/smoke_test.py` (Smoke test 3 query).
3. `ffprobe artifacts/samples/*.mp4` (Kiểm tra 3 sample MP4).
4. `sqlite3 chemistry.db 'SELECT job_id, status FROM jobs;'` (Kiểm tra DB).

## Progress

| WP | Status | Notes |
|---|---|---|
| WP-01 | pending | Scaffold, models, VideoConfig, VideoScript, LLM factory |
| WP-02 | pending | JobRepository, startup stuck jobs reset |
| WP-03 | pending | LangGraph StateGraph topology, node stubs |
| WP-04 | pending | Structured Output script_node, validator_node |
| WP-05 | pending | Parallel chunk audio & slides, FFmpeg sync assembler |
| WP-06 | pending | JobQueue, AsyncioWorkerQueue, API endpoints |
| WP-07 | pending | Unit tests suite |
| WP-08 | pending | Smoke test & 3 sample MP4s |
| WP-09 | pending | README & ARCHITECTURE docs |
