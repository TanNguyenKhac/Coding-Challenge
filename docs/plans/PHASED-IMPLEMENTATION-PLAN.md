# 🗺️ Phased Implementation Plan & Milestone Roadmap: AI Chemistry Video Engine

- **Project**: AI Chemistry Video Request Engine
- **Tracking ID**: CHG-002
- **Related Specs**: [`SPEC-01`](../specs/SPEC-01-api-persistence.md), [`SPEC-02`](../specs/SPEC-02-queue-worker.md), [`SPEC-03`](../specs/SPEC-03-llm-structured-script.md), [`SPEC-04`](../specs/SPEC-04-media-chunk-assembly.md), [`SPEC-05`](../specs/SPEC-05-testing-verification.md)
- **Business Requirements Authority**: [`docs/biz.md`](../biz.md), [`artifacts/handoffs/CHG-002-discovery.yaml`](../../artifacts/handoffs/CHG-002-discovery.yaml)
- **Active Execution Plan**: [`docs/plans/active/CHG-002-langgraph-sqlalchemy-mvp.md`](active/CHG-002-langgraph-sqlalchemy-mvp.md)
- **Status**: Ready for Execution

---

## 1. Tổng quan lộ trình triển khai (Milestone Overview)

Lộ trình phát triển được chia thành **6 Milestones (Phases)** tuần tự, có ranh giới kỹ thuật rõ ràng, kiểm thử độc lập ở từng pha và liên kết trực tiếp với các tài liệu đặc tả (Specs) và yêu cầu nghiệp vụ (Business Requirements).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Milestone 1: Foundation, Storage & Configuration (WP-01, WP-02)             │
│ [Config, Schemas, ORM Model, JobRepository, Session Factory, LLM Factory]   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Milestone 2: AI Pipeline, Structured Output & Graph Topology (WP-03, WP-04) │
│ [LangGraph StateGraph, Structured Output VideoScript, Validator & Retry]    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Milestone 3: Media Engine & Parallel Chunk Workers (WP-05)                  │
│ [Parallel Audio TTS + Pyttsx3, Parallel Slides Pillow, FFmpeg Assembler]    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Milestone 4: Concurrency Queue, Background Workers & Web API (WP-06)        │
│ [JobQueue, AsyncioWorkerQueue, Independent Worker Session, 4 REST APIs]     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Milestone 5: Verification, Repeatability & 3 Sample Artifacts (WP-07, WP-08)│
│ [Unit Test Suite, 2-Run Repeatable Smoke Test, 3 Pre-generated Sample MP4s] │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Milestone 6: Documentation, Architecture Audit & Handoff (WP-09)            │
│ [README.md, ARCHITECTURE.md, Verification Ledger, Final Handoff]            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Chi tiết từng Milestone & Kế hoạch Thực thi

---

### 🟢 MILESTONE 1: Foundation, Storage & Configuration

- **Mục tiêu**: Thiết lập cấu trúc dự án, môi trường dependencies, cấu hình pydantic-settings, mô hình cơ sở dữ liệu SQLAlchemy 2.0 (SQLite), các Pydantic schema cốt lõi, LLM factory, và tầng truy cập dữ liệu `JobRepository`.
- **Work Packages**: `WP-01`, `WP-02`
- **Tài liệu tham chiếu**: [`SPEC-01`](../specs/SPEC-01-api-persistence.md), [`SPEC-03 §2`](../specs/SPEC-03-llm-structured-script.md)
- **Yêu cầu nghiệp vụ (`docs/biz.md`)**: `REQ-001`, `REQ-006`, `REQ-010`, `EVD-001`, `EVD-005`, `EVD-012`, `EVD-015`, `EVD-016`

#### Các thành phần bàn giao (Deliverables):
1. `requirements.txt` và `.env.example` với đầy đủ dependencies: FastAPI, SQLAlchemy, aiosqlite, LangGraph, LangChain, Pillow, gTTS, pyttsx3, ffmpeg-python, pydantic-settings.
2. `app/config.py`: Đọc cấu hình biến môi trường (`DATABASE_URL`, `ARTIFACTS_DIR`, `CODEX_API_BASE`, `ANTHROPIC_API_KEY`, `MAX_RETRIES`, `MAX_CONCURRENT_JOBS`).
3. `app/database.py`: Khởi tạo async engine, `async_session_factory`, và hàm `create_tables()`.
4. `app/models/job.py`: SQLAlchemy ORM model `Job` (chứa trường `job_id`, `concept`, `config` JSON, `status`, `error_reason`, `artifact_path`, `retry_count`, `created_at`, `updated_at`).
5. `app/schemas/job.py`: Pydantic models `VideoConfig`, `JobCreate`, `JobResponse`, `JobStatus`.
6. `app/schemas/script.py`: Pydantic models `ScriptChunk`, `VideoScript`.
7. `app/llm_factory.py`: Hàm `build_llm()` hỗ trợ Codex (OpenAI-compatible primary), Anthropic Haiku (fallback), FakeListChatModel (test).
8. `app/repositories/job_repository.py`: Triển khai đầy đủ các method: `create()`, `get()`, `list_all()`, `update_status()`, `reset_stuck_jobs()`.

#### Tiêu chí hoàn thành (Exit Criteria / DoD):
- [x] Import toàn bộ models, schemas, config không có lỗi cú pháp.
- [x] Tạo thành công file `chemistry.db` với bảng `jobs` qua `asyncio.run(create_tables())`.
- [x] Chạy test `tests/test_api.py::TestJobRepository` pass 100% (tạo, đọc, cập nhật status, reset stuck jobs).

#### Lệnh kiểm chứng:
```bash
python -c "from app.models.job import Job, JobStatus; from app.schemas.job import JobCreate, JobResponse; from app.schemas.script import VideoScript; print('Imports OK')"
python -c "import asyncio; from app.database import create_tables; asyncio.run(create_tables()); print('DB Table Created OK')"
pytest tests/test_api.py::TestJobRepository -v
```

---

### 🟢 MILESTONE 2: AI Pipeline, Structured Output & Graph Topology

- **Mục tiêu**: Xây dựng StateGraph của LangGraph, triển khai `script_node` với **100% Pydantic Structured Output (Zero Regex)**, triển khai `validator_node` kiểm soát chất lượng sư phạm và điều hướng Retry loop.
- **Work Packages**: `WP-03`, `WP-04`
- **Tài liệu tham chiếu**: [`SPEC-03`](../specs/SPEC-03-llm-structured-script.md), [`SPEC-01 §2`](../specs/SPEC-01-api-persistence.md)
- **Yêu cầu nghiệp vụ (`docs/biz.md`)**: `REQ-005`, `REQ-008`, `REQ-010`, `EVD-006`, `EVD-011`, `EVD-014`, `EVD-018`

#### Các thành phần bàn giao (Deliverables):
1. `app/pipeline/state.py`: Định nghĩa `VideoGenerationState` TypedDict.
2. `app/pipeline/graph.py`: Định nghĩa `StateGraph` với 5 nodes và conditional routing cho retry loop (`pass`, `retry`, `failed`).
3. `app/pipeline/nodes/script_node.py`: Gọi LLM qua `llm.with_structured_output(VideoScript)` kết hợp chemistry system prompt, trả về trực tiếp instance `VideoScript` (tuyệt đối không regex).
4. `app/pipeline/nodes/validator_node.py`: Hàm `validate_script_node` kiểm tra `len(chunks) >= 3`, tiêu đề và nội dung không rỗng; hàm `script_router` điều hướng retry nếu `retry_count <= MAX_RETRIES`.

#### Tiêu chí hoàn thành (Exit Criteria / DoD):
- [x] Graph compile thành công không có chu trình lỗi hoặc dangling node.
- [x] `script_node` parse chính xác kịch bản thành Pydantic `VideoScript`.
- [x] Validator phát hiện chính xác kịch bản thiếu phân đoạn và kích hoạt retry tự động (tối đa 2 lần).

#### Lệnh kiểm chứng:
```bash
pytest tests/test_pipeline.py::TestGraphTopology -v
pytest tests/test_pipeline.py::TestScriptNode tests/test_pipeline.py::TestValidatorNode -v
```

---

### 🟢 MILESTONE 3: Media Engine & Parallel Chunk Workers

- **Mục tiêu**: Xây dựng các worker xử lý song song (fan-out) cho Audio TTS và Slide images, triển khai `VideoAssembler` interface với `FFmpegAssembler` (đồng bộ thời lượng hiển thị slide theo độ dài audio per chunk) và `MockAssembler`.
- **Work Packages**: `WP-05`
- **Tài liệu tham chiếu**: [`SPEC-04`](../specs/SPEC-04-media-chunk-assembly.md)
- **Yêu cầu nghiệp vụ (`docs/biz.md`)**: `REQ-005`, `REQ-009`, `REQ-011`, `EVD-003`, `EVD-007`, `EVD-017`

#### Các thành phần bàn giao (Deliverables):
1. `app/pipeline/assembler.py`: `VideoAssembler` ABC, `MockAssembler` (tạo MP4 stub nhanh cho test), và `FFmpegAssembler` (ghép video thật bằng FFmpeg concat & duration sync).
2. `app/pipeline/nodes/audio_node.py`: Sinh $N$ file audio chunks song song qua `asyncio.gather`, gTTS với fallback tự động sang `pyttsx3`.
3. `app/pipeline/nodes/slides_node.py`: Render $N$ slide ảnh 1280×720 song song bằng Pillow với giao diện Dark Theme bài giảng hóa học.
4. `app/pipeline/nodes/assembler_node.py`: Tích hợp gọi `VideoAssembler.assemble()` vào StateGraph.

#### Tiêu chí hoàn thành (Exit Criteria / DoD):
- [x] Audio node tạo đủ $N$ file MP3 tương ứng với $N$ chunks kịch bản.
- [x] Slide node tạo đủ $N$ file PNG kích thước 1280×720 sắc nét.
- [x] `FFmpegAssembler` tạo ra video MP4 có audio và hình ảnh ăn khớp hoàn toàn về thời lượng từng phân đoạn.
- [x] `MockAssembler` hoàn tất render stub trong < 50ms.

#### Lệnh kiểm chứng:
```bash
pytest tests/test_pipeline.py::TestVideoNodes -v
```

---

### 🟢 MILESTONE 4: Concurrency Queue, Background Workers & Web API

- **Mục tiêu**: Xây dựng tầng hàng đợi `JobQueue` và `AsyncioWorkerQueue` kiểm soát concurrency tải render (`MAX_CONCURRENT_JOBS = 2`), triển khai `job_service.py` với session DB độc lập, hoàn thiện 4 REST API endpoints và static file mount.
- **Work Packages**: `WP-06`
- **Tài liệu tham chiếu**: [`SPEC-01`](../specs/SPEC-01-api-persistence.md), [`SPEC-02`](../specs/SPEC-02-queue-worker.md)
- **Yêu cầu nghiệp vụ (`docs/biz.md`)**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-007`, `EVD-001`, `EVD-002`, `EVD-013`, `EVD-019`

#### Các thành phần bàn giao (Deliverables):
1. `app/services/queue.py`: `JobQueue` ABC và `AsyncioWorkerQueue` quản lý worker pool và backpressure.
2. `app/services/job_service.py`: `run_pipeline(job_id)` tự tạo DB session qua `async with async_session_factory() as session:` và thực thi StateGraph.
3. `app/api/v1/jobs.py`: 4 route handlers (`POST /jobs`, `GET /jobs`, `GET /jobs/{id}`, `GET /jobs/{id}/artifact`).
4. `app/main.py`: Khởi tạo FastAPI app, lifespan (tự động chạy startup stuck jobs reset, start/stop worker pool), mount `/artifacts` static files.

#### Tiêu chí hoàn thành (Exit Criteria / DoD):
- [x] `POST /api/v1/jobs` phản hồi mã 201 trong < 50ms, không block HTTP thread.
- [x] Worker pool kiểm soát không quá 2 job render đồng thời.
- [x] `GET /api/v1/jobs/{id}/artifact` trả về đúng file video MP4 khi status là complete.

#### Lệnh kiểm chứng:
```bash
pytest tests/test_api.py tests/test_queue.py -v
```

---

### 🟢 MILESTONE 5: Comprehensive Verification, Repeatability & Sample Artifacts

- **Mục tiêu**: Hoàn thiện bộ unit test toàn diện, thực thi kịch bản Smoke Test lặp lại 2 lần liên tiếp trên 3 câu hỏi hóa học bắt buộc, tạo và commit 3 video MP4 mẫu thực tế vào `artifacts/samples/`.
- **Work Packages**: `WP-07`, `WP-08`
- **Tài liệu tham chiếu**: [`SPEC-05`](../specs/SPEC-05-testing-verification.md)
- **Yêu cầu nghiệp vụ (`docs/biz.md`)**: `REQ-009`, `EVD-004`, `EVD-006`, `EVD-009`, `AC-001` đến `AC-010`

#### Các thành phần bàn giao (Deliverables):
1. `tests/conftest.py`: Fixtures In-Memory SQLite DB, Mock LLM, Mock Assembler, Async HTTP Client.
2. `tests/test_api.py`, `tests/test_pipeline.py`, `tests/test_queue.py`: Bộ unit test đầy đủ bao phủ 100% luồng nghiệp vụ.
3. `scripts/smoke_test.py`: Script tự động gửi 3 câu hỏi hóa học bắt buộc, poll trạng thái và kiểm tra artifact.
4. `scripts/generate_samples.py`: Script sinh 3 video MP4 mẫu thực tế.
5. 3 File video mẫu được commit trong `artifacts/samples/`:
   - `artifacts/samples/job-ph-scale.mp4`
   - `artifacts/samples/job-covalent-bonds.mp4`
   - `artifacts/samples/job-ionic-vs-covalent.mp4`
6. `artifacts/samples/README.md`: Bảng thông số kỹ thuật chi tiết của 3 video mẫu.

#### Tiêu chí hoàn thành (Exit Criteria / DoD):
- [x] Toàn bộ unit tests pass trong < 5s mà không cần internet hay external dependencies.
- [x] Chạy `scripts/smoke_test.py` thành công 2 lần liên tiếp trên server thật.
- [x] 3 file MP4 mẫu phát mượt mà, có đầy đủ âm thanh thuyết minh và hình ảnh đồng bộ.

#### Lệnh kiểm chứng:
```bash
pytest tests/ -v --tb=short
python scripts/smoke_test.py   # Run 1
python scripts/smoke_test.py   # Run 2 (Repeatability check)
python scripts/generate_samples.py
ffprobe artifacts/samples/*.mp4
```

---

### 🟢 MILESTONE 6: Documentation, Architecture Audit & Handoff

- **Mục tiêu**: Hoàn tất toàn bộ tài liệu hướng dẫn (`README.md`), tài liệu kiến trúc chuyên sâu (`ARCHITECTURE.md`), kiểm tra ma trận yêu cầu và hoàn tất handoff bàn giao.
- **Work Packages**: `WP-09`
- **Tài liệu tham chiếu**: `README.md`, `ARCHITECTURE.md`, [`CHG-002-discovery.yaml`](../../artifacts/handoffs/CHG-002-discovery.yaml)
- **Yêu cầu nghiệp vụ (`docs/biz.md`)**: `REQ-012`, `REQ-013`, `AC-011`, `AC-012`

#### Các thành phần bàn giao (Deliverables):
1. `README.md` hoàn chỉnh (cài đặt, cấu hình, curl examples, lệnh test, video mẫu).
2. `ARCHITECTURE.md` hoàn chỉnh (sơ đồ StateGraph, worker queue topology, bảng phân tích chi phí $0.0021/video, ma trận reliability).
3. Cập nhật trạng thái `docs/plans/active/CHG-002-langgraph-sqlalchemy-mvp.md` thành Completed sau khi toàn bộ verification pass.

---

## 3. Ma trận Truy vết (Traceability & Requirement Mapping Matrix)

| Business Requirement (`docs/biz.md`) | Spec Tham Chiếu | Work Package | Milestone | Phương Thức Kiểm Chứng |
|---|---|---|---|---|
| **REQ-001**: POST /jobs (concept + config) | [`SPEC-01`](../specs/SPEC-01-api-persistence.md) | WP-01, WP-06 | M1, M4 | `tests/test_api.py::test_create_job` |
| **REQ-002**: GET /jobs (list all) | [`SPEC-01`](../specs/SPEC-01-api-persistence.md) | WP-01, WP-06 | M1, M4 | `tests/test_api.py::test_list_jobs` |
| **REQ-003**: GET /jobs/{id} (status/detail) | [`SPEC-01`](../specs/SPEC-01-api-persistence.md) | WP-01, WP-06 | M1, M4 | `tests/test_api.py::test_get_job_detail` |
| **REQ-004**: GET /jobs/{id}/artifact (MP4) | [`SPEC-01`](../specs/SPEC-01-api-persistence.md) | WP-01, WP-06 | M1, M4 | `tests/test_api.py::test_get_artifact` |
| **REQ-005**: LangGraph StateGraph & Chunks | [`SPEC-03`](../specs/SPEC-03-llm-structured-script.md), [`SPEC-04`](../specs/SPEC-04-media-chunk-assembly.md) | WP-03, WP-04, WP-05 | M2, M3 | `tests/test_pipeline.py::test_full_graph` |
| **REQ-006**: SQLAlchemy SQLite Persistence | [`SPEC-01`](../specs/SPEC-01-api-persistence.md) | WP-01, WP-02 | M1 | `tests/test_api.py::TestJobRepository` |
| **REQ-007**: JobQueue & Concurrency Limiter | [`SPEC-02`](../specs/SPEC-02-queue-worker.md) | WP-06 | M4 | `tests/test_queue.py::test_concurrency` |
| **REQ-008**: Structured Output & Retry Loop | [`SPEC-03`](../specs/SPEC-03-llm-structured-script.md) | WP-04 | M2 | `tests/test_pipeline.py::TestValidator` |
| **REQ-009**: MP4 Video Artifact & Duration Sync | [`SPEC-04`](../specs/SPEC-04-media-chunk-assembly.md), [`SPEC-05`](../specs/SPEC-05-testing-verification.md) | WP-05, WP-08 | M3, M5 | `ffprobe artifacts/samples/*.mp4` |
| **REQ-010**: LLM Provider Interface (Codex/Anthropic) | [`SPEC-03`](../specs/SPEC-03-llm-structured-script.md) | WP-01, WP-04 | M1, M2 | `tests/test_pipeline.py::test_llm_factory` |
| **REQ-011**: VideoAssembler ABC (FFmpeg/Mock) | [`SPEC-04`](../specs/SPEC-04-media-chunk-assembly.md) | WP-05 | M3 | `tests/test_pipeline.py::TestVideoNodes` |
| **REQ-012**: README.md Guide | `README.md` | WP-09 | M6 | Manual checklist inspection |
| **REQ-013**: ARCHITECTURE.md Blueprint | `ARCHITECTURE.md` | WP-09 | M6 | Cost & Reliability table review |
| **3 Required Concepts (pH, Covalent, Ionic)** | [`SPEC-05`](../specs/SPEC-05-testing-verification.md) | WP-08 | M5 | `scripts/smoke_test.py` (2-run repeat) |

---

## 4. Quản lý Rủi ro & Kế hoạch Phục hồi (Risk Management & Mitigation)

| Rủi ro Kỹ thuật | Xác suất | Tác động | Biện pháp Phòng ngừa & Xử lý |
|---|---|---|---|
| **Server Crash/Restart làm stuck Job** | Trung bình | Cao | Lifespan hook gọi `JobRepository.reset_stuck_jobs()` tự động chuyển `generating` $\to$ `failed` ("server_restart"). |
| **LLM Output sai Format / Parse Error** | Thấp | Cao | Sử dụng 100% Pydantic Structured Output (`with_structured_output`), loại bỏ hoàn toàn regex. |
| **Lỗi Rate Limit hoặc mất mạng TTS** | Trung bình | Trung bình | Tự động fallback từ `gTTS` sang `pyttsx3` offline cục bộ. |
| **FFmpeg Desync giữa Slide và Lời đọc** | Thấp | Cao | `FFmpegAssembler` tự đo độ dài file audio per chunk và gán thời lượng hiển thị slide tương ứng. |
| **Quá tải CPU do Render đồng thời** | Cao | Cao | `AsyncioWorkerQueue` giới hạn `MAX_CONCURRENT_JOBS = 2`, hàng đợi in-process điều phối tuần tự. |
| **Session DB bị đóng sớm trong Worker** | Trung bình | Cao | Worker tự quản lý DB session qua `async with async_session_factory() as session:`, tách biệt với HTTP scope. |
