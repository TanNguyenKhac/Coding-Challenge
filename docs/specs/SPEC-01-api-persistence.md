# Functional Specification: SPEC-01 — API Endpoints & Persistence Layer

- **Module**: `app.api.v1.jobs`, `app.models.job`, `app.schemas.job`, `app.repositories.job_repository`, `app.database`
- **Scope**: REST API endpoints, Pydantic validation schemas, SQLAlchemy ORM models, Database repository, Session lifecycle.
- **Related Plan**: CHG-002 (WP-01, WP-02, WP-06)
- **Status**: Approved for Implementation

---

## 1. Business Context & Objective

Hệ thống cung cấp giao diện RESTful HTTP để người học (hoặc frontend client) gửi yêu cầu tạo video giải thích khái niệm hóa học (`concept`), tùy chỉnh các thông số video (`VideoConfig`), theo dõi trạng thái tiến trình bất đồng bộ (`status: pending | generating | complete | failed`), và tải về artifact video MP4 sau khi hoàn tất.

Dữ liệu trạng thái của Job cần được lưu trữ bền vững (persistence) qua SQLite/SQLAlchemy 2.0 để không bị mất khi ứng dụng reload, đồng thời đảm bảo phân định rõ ranh giới: `JobRepository` là thành phần duy nhất được phép ghi/đọc cơ sở dữ liệu.

---

## 2. Technical Requirements

### 2.1 Database & ORM Model (`app/models/job.py`)

- **Bảng**: `jobs`
- **Engine**: SQLite với async driver `aiosqlite` (`sqlite+aiosqlite:///./chemistry.db`).
- **Trường dữ liệu**:

| Cột | Kiểu dữ liệu (SQLAlchemy) | Nullable | Mô tả / Ràng buộc |
|---|---|---|---|
| `job_id` | `String(36)` (UUID v4) | No | Primary Key, định danh duy nhất của Job |
| `concept` | `Text` | No | Khái niệm/câu hỏi hóa học người dùng nhập |
| `config` | `JSON` | No | Cấu hình video (`VideoConfig` serialized JSON) |
| `status` | `Enum(JobStatus)` | No | Trạng thái: `pending`, `generating`, `complete`, `failed` |
| `error_reason` | `Text` | Yes | Lý do thất bại nếu `status == failed` |
| `artifact_path` | `String(255)` | Yes | Đường dẫn file MP4 trên đĩa nếu `status == complete` |
| `retry_count` | `Integer` | No | Số lần retry script generation (mặc định: 0) |
| `created_at` | `DateTime(timezone=True)` | No | Thời điểm tạo job (mặc định `utcnow`) |
| `updated_at` | `DateTime(timezone=True)` | No | Thời điểm cập nhật cuối (auto on update) |

### 2.2 Pydantic Schemas (`app/schemas/job.py`)

```python
from datetime import datetime
from enum import Enum
from typing import Optional, Tuple
from pydantic import BaseModel, Field

class JobStatus(str, Enum):
    pending = "pending"
    generating = "generating"
    complete = "complete"
    failed = "failed"

class VideoConfig(BaseModel):
    target_duration_sec: int = Field(default=60, ge=15, le=300, description="Thời lượng mục tiêu (giây)")
    target_audience: str = Field(default="high_school", description="Đối tượng: high_school, university, beginner")
    aspect_ratio: str = Field(default="16:9", description="Tỉ lệ khung hình: 16:9, 9:16")
    resolution: Tuple[int, int] = Field(default=(1280, 720), description="Độ phân giải (width, height)")
    language: str = Field(default="vi", description="Ngôn ngữ thuyết minh")
    voice_gender: str = Field(default="neutral", description="Giọng đọc TTS: male, female, neutral")

class JobCreate(BaseModel):
    concept: str = Field(..., min_length=3, max_length=500, description="Khái niệm hóa học cần giải thích")
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

    class Config:
        from_attributes = True
```

### 2.3 API Endpoints Specification (`app/api/v1/jobs.py`)

#### `POST /api/v1/jobs`
- **Mục đích**: Tiếp nhận yêu cầu tạo video mới, lưu job `pending` vào DB, đẩy vào `JobQueue` và phản hồi ngay.
- **Request Body**: `JobCreate`
- **Response Status**: `201 Created`
- **Response Body**: `JobResponse` (với `status: "pending"`, `artifact_url: null`)

#### `GET /api/v1/jobs`
- **Mục đích**: Liệt kê tất cả các job đã tạo trong hệ thống theo thứ tự mới nhất trước.
- **Response Status**: `200 OK`
- **Response Body**: `list[JobResponse]`

#### `GET /api/v1/jobs/{job_id}`
- **Mục đích**: Lấy thông tin chi tiết và trạng thái hiện tại của một job.
- **Path Param**: `job_id` (string UUID)
- **Response Status**:
  - `200 OK`: Trả về `JobResponse` (nếu `complete`, trường `artifact_url` có dạng `/artifacts/{job_id}.mp4`).
  - `404 Not Found`: `{ "detail": "Job not found" }` nếu `job_id` không tồn tại.

#### `GET /api/v1/jobs/{job_id}/artifact`
- **Mục đích**: Tải trực tiếp file video MP4 hoàn chỉnh.
- **Path Param**: `job_id` (string UUID)
- **Response Status**:
  - `200 OK`: Trả về `FileResponse(path, media_type="video/mp4", filename="job_{job_id}.mp4")`.
  - `400 Bad Request`: `{ "detail": "Job is not complete yet (status: <status>)" }` nếu job chưa `complete`.
  - `404 Not Found`: `{ "detail": "Job or artifact file not found" }`.

---

## 3. Repository & Session Management Contract (`app/repositories/job_repository.py`)

```python
class JobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, concept: str, config: dict | None = None) -> Job:
        """Tạo job mới với status pending."""
        ...

    async def get(self, job_id: str) -> Job | None:
        """Truy vấn job theo UUID."""
        ...

    async def list_all(self) -> list[Job]:
        """Lấy danh sách tất cả jobs sắp xếp theo created_at giảm dần."""
        ...

    async def update_status(
        self,
        job_id: str,
        status: JobStatus,
        artifact_path: str | None = None,
        error_reason: str | None = None,
        retry_count: int | None = None,
    ) -> None:
        """Cập nhật trạng thái và metadata của job."""
        ...

    async def reset_stuck_jobs(self) -> None:
        """Được gọi khi server startup: reset tất cả job 'generating' về 'failed' với error_reason 'server_restart'."""
        ...
```

### Quy tắc quản lý Async DB Session:
1. **Tại API Request**: Sử dụng FastAPI Dependency `get_session()` (tự động commit/rollback/close theo scope của HTTP request).
2. **Tại Background Worker / JobQueue**: **Không dùng request session**. Worker phải tự tạo session riêng bằng `async with async_session_factory() as session:` và truyền vào `JobRepository(session)`.

---

## 4. Definition of Done (DoD)

1. [x] Bảng `jobs` được tạo tự động khi ứng dụng khởi động (`create_tables()`).
2. [x] 4 API endpoints hoạt động chuẩn xác theo REST convention với response schemas đúng chuẩn Pydantic.
3. [x] Static files được mount tại `/artifacts` qua `FastAPI.mount()`.
4. [x] Xử lý lỗi đầy đủ: 400 (chưa complete), 404 (không tìm thấy job/file), 422 (sai validation schema).
5. [x] Method `reset_stuck_jobs()` đổi toàn bộ job `generating` còn sót từ phiên trước thành `failed` ("server_restart").

---

## 5. Verification Checklist & Unit Test Matrix

| ID | Test Case | Đầu vào | Kết quả mong đợi |
|---|---|---|---|
| TC-01-01 | Tạo Job hợp lệ | `POST /api/v1/jobs` với `{ "concept": "How does the pH scale work?" }` | 201 Created, `status == "pending"`, `job_id` hợp lệ, `config` nhận default |
| TC-01-02 | Tạo Job kèm Custom Config | `POST /api/v1/jobs` với `{ "concept": "...", "config": { "target_duration_sec": 45 } }` | 201 Created, `config.target_duration_sec == 45` |
| TC-01-03 | Tạo Job rỗng / không hợp lệ | `POST /api/v1/jobs` với `{ "concept": "ab" }` (ngắn hơn 3 ký tự) | 422 Unprocessable Entity |
| TC-01-04 | Lấy danh sách Jobs | `GET /api/v1/jobs` | 200 OK, trả về list chứa các job đã tạo |
| TC-01-05 | Lấy chi tiết Job tồn tại | `GET /api/v1/jobs/{valid_id}` | 200 OK, đúng thông tin `job_id` và `status` |
| TC-01-06 | Lấy chi tiết Job không tồn tại | `GET /api/v1/jobs/{unknown_uuid}` | 404 Not Found, detail "Job not found" |
| TC-01-07 | Tải artifact khi job chưa complete | `GET /api/v1/jobs/{pending_id}/artifact` | 400 Bad Request, detail "Job is not complete yet" |
| TC-01-08 | Tải artifact khi job đã complete | `GET /api/v1/jobs/{complete_id}/artifact` (có file mp4) | 200 OK, Content-Type `video/mp4` |
| TC-01-09 | Server Startup Reset Stuck Jobs | Khởi tạo job có `status="generating"` trong DB rồi gọi `reset_stuck_jobs()` | Job chuyển thành `status="failed"`, `error_reason="server_restart"` |
