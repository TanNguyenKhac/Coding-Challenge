# Functional Specification: SPEC-05 — Testing, Verification & Sample Generation

- **Module**: `tests/*`, `scripts/smoke_test.py`, `scripts/generate_samples.py`, `artifacts/samples/*`
- **Scope**: Unit test suite, In-memory test fixtures, Concurrency queue tests, 2-run repeatability smoke test, Pre-generated sample video generation.
- **Related Plan**: CHG-002 (WP-07, WP-08)
- **Status**: Approved for Implementation

---

## 1. Business Context & Objective

Để chứng minh hệ thống vận hành tin cậy trong thực tế (không chỉ chạy may mắn một lần mà ổn định qua các lần chạy lặp lại dưới sự bất định của LLM), hệ thống cần:
1. **Bộ Unit Tests toàn diện và độc lập**: 100% test pass mà không cần internet, không tốn API key và không yêu cầu cài đặt FFmpeg binary.
2. **Smoke Test Lặp lại (Repeatability Proof)**: Script kiểm thử đầu-cuối chạy thành công **2 lần liên tiếp** trên cả **3 câu hỏi hóa học bắt buộc**:
   - `How does the pH scale work?`
   - `Why do atoms form covalent bonds?`
   - `What is the difference between ionic and covalent bonding?`
3. **Pre-generated Committed Artifacts**: Tạo sẵn 3 video MP4 mẫu thực tế và lưu vào `artifacts/samples/` để người đánh giá có thể kiểm tra chất lượng video ngay lập tức.

---

## 2. Test Architecture & Fixtures Design (`tests/conftest.py`)

Để đảm bảo tính cô lập và tốc độ chạy test nhanh (< 5 giây cho toàn bộ test suite):

```python
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from app.models.job import Job
from app.database import Base
from app.pipeline.assembler import MockAssembler
from app.schemas.script import VideoScript, ScriptChunk
from app.main import app

# 1. In-Memory SQLite Database Engine Fixture
@pytest_asyncio.fixture
async def test_db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

# 2. Mock LLM Fixture with Valid Structured Output
@pytest.fixture
def mock_video_script():
    return VideoScript(
        title="Understanding the pH Scale",
        summary="The pH scale measures acidity and alkalinity based on hydrogen ion concentration.",
        chunks=[
            ScriptChunk(
                chunk_id=0,
                heading="Introduction to Acids and Bases",
                narration="Acids and bases are everywhere in our daily lives from lemon juice to soap.",
                visual_notes="Draw lemon (acid, low pH) and soap (base, high pH) on a scale."
            ),
            ScriptChunk(
                chunk_id=1,
                heading="The Hydrogen Ion (H+) Mechanism",
                narration="pH stands for potential of Hydrogen. Lower pH means higher concentration of H+ ions.",
                visual_notes="Show H+ ions concentration zooming in from 1 to 14 logarithmic scale."
            ),
            ScriptChunk(
                chunk_id=2,
                heading="The 0 to 14 Scale Summary",
                narration="7 is neutral like pure water, below 7 is acidic, and above 7 is basic or alkaline.",
                visual_notes="Color gradient scale from red (0) to green (7) to purple (14)."
            )
        ]
    )

# 3. Mock Assembler Fixture
@pytest.fixture
def mock_assembler():
    return MockAssembler()

# 4. Async HTTP Test Client
@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
```

---

## 3. Unit Test Modules Specification

### 3.1 API & Repository Tests (`tests/test_api.py`)
- `test_create_job_default_config`: POST /jobs tạo job pending, nhận config mặc định.
- `test_create_job_custom_config`: POST /jobs nhận `target_duration_sec`, `aspect_ratio`.
- `test_list_jobs`: GET /jobs trả về danh sách đầy đủ.
- `test_get_job_detail_success`: GET /jobs/{id} trả về chi tiết.
- `test_get_job_detail_not_found`: GET /jobs/{invalid_id} trả về 404.
- `test_get_artifact_pending`: GET /jobs/{id}/artifact khi chưa complete trả về 400.
- `test_get_artifact_complete`: GET /jobs/{id}/artifact khi complete trả về file video.
- `test_startup_reset_stuck_jobs`: Kiểm tra reset trạng thái job từ "generating" thành "failed" ("server_restart").

### 3.2 Pipeline & LangGraph Tests (`tests/test_pipeline.py`)
- `test_structured_script_node`: Kiểm tra `script_node` gán đúng `VideoScript` Pydantic instance.
- `test_validator_node_pass`: Script hợp lệ trả về routing `"pass"`.
- `test_validator_node_retry`: Script < 3 chunks tăng `retry_count` và routing `"retry"`.
- `test_validator_node_max_retry_failed`: Vượt quá max retries chuyển sang `"failed"`.
- `test_parallel_audio_generation`: Xử lý song song N audio chunks.
- `test_parallel_slides_generation`: Xử lý song song N slides 1280×720.
- `test_full_graph_invocation`: Chạy trọn vẹn LangGraph pipeline từ START đến END với Mock providers.

### 3.3 Worker Queue Tests (`tests/test_queue.py`)
- `test_queue_worker_concurrency`: Đẩy 4 jobs vào queue có `concurrency=2`, chứng minh tối đa 2 jobs chạy đồng thời.
- `test_queue_graceful_shutdown`: Dừng worker pool an toàn khi còn task.

---

## 4. End-to-End Smoke Test Specification (`scripts/smoke_test.py`)

Kịch bản chạy kiểm thử 3 chủ đề hóa học bắt buộc qua API server thật:

```python
import asyncio
import httpx
import time

REQUIRED_CONCEPTS = [
    "How does the pH scale work?",
    "Why do atoms form covalent bonds?",
    "What is the difference between ionic and covalent bonding?"
]

BASE_URL = "http://127.0.0.1:8000/api/v1"

async def test_single_query(client: httpx.AsyncClient, concept: str) -> str:
    print(f"\n[+] Submitting concept: '{concept}'")
    resp = await client.post(f"{BASE_URL}/jobs", json={"concept": concept})
    assert resp.status_code == 201, f"Create failed: {resp.text}"
    job_id = resp.json()["job_id"]
    print(f"    Job ID: {job_id}, Status: pending")

    # Poll status every 2 seconds until complete or timeout (120s)
    start_time = time.time()
    while time.time() - start_time < 120:
        await asyncio.sleep(2)
        status_resp = await client.get(f"{BASE_URL}/jobs/{job_id}")
        data = status_resp.json()
        status = data["status"]
        print(f"    Polling job {job_id}: {status} ({int(time.time() - start_time)}s)")
        if status == "complete":
            # Verify artifact endpoint
            art_resp = await client.get(f"{BASE_URL}/jobs/{job_id}/artifact")
            assert art_resp.status_code == 200
            assert art_resp.headers["content-type"] == "video/mp4"
            print(f"    [SUCCESS] Video generated: {data.get('artifact_url')}")
            return job_id
        elif status == "failed":
            raise RuntimeError(f"Job {job_id} failed with reason: {data.get('error_reason')}")

    raise TimeoutError(f"Job {job_id} timed out after 120s")

async def run_smoke_test():
    print("=== STARTING SMOKE TEST SUITE ===")
    async with httpx.AsyncClient(timeout=130.0) as client:
        for concept in REQUIRED_CONCEPTS:
            await test_single_query(client, concept)
    print("\n=== ALL 3 REQUIRED CHEMISTRY QUERIES PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
```

---

## 5. Sample Generation Script (`scripts/generate_samples.py`)

- Thực thi tương tự `smoke_test.py`.
- Tải file video kết quả của 3 câu hỏi bắt buộc và lưu cố định vào thư mục `artifacts/samples/`:
  - `artifacts/samples/job-ph-scale.mp4`
  - `artifacts/samples/job-covalent-bonds.mp4`
  - `artifacts/samples/job-ionic-vs-covalent.mp4`
- Thêm file `artifacts/samples/README.md` ghi nhận thông số metadata (thời lượng, dung lượng, độ phân giải).

---

## 6. Definition of Done (DoD)

1. [x] `pytest tests/ -v` pass 100% không có lỗi, không có XFAIL, thời gian thực thi < 10 giây.
2. [x] `scripts/smoke_test.py` chạy thành công liên tiếp 2 lần với cả 3 query hóa học bắt buộc.
3. [x] 3 file video MP4 mẫu tồn tại trong `artifacts/samples/`, kiểm tra qua `ffprobe` có đầy đủ stream H.264 video và AAC audio.

---

## 7. Verification Checklist & Command Execution

```bash
# 1. Chạy toàn bộ Unit Test Suite
pytest tests/ -v --tb=short

# 2. Khởi động server trong background hoặc terminal riêng
uvicorn app.main:app --host 127.0.0.1 --port 8000

# 3. Chạy Smoke Test lần 1 (Repeatability Check 1)
python scripts/smoke_test.py

# 4. Chạy Smoke Test lần 2 (Repeatability Check 2)
python scripts/smoke_test.py

# 5. Sinh và lưu 3 sample videos
python scripts/generate_samples.py

# 6. Kiểm tra cấu trúc stream của sample videos
ffprobe artifacts/samples/job-ph-scale.mp4
ffprobe artifacts/samples/job-covalent-bonds.mp4
ffprobe artifacts/samples/job-ionic-vs-covalent.mp4
```
