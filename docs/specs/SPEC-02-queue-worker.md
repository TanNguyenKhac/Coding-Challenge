# Functional Specification: SPEC-02 — Queue Abstraction & Worker Pool

- **Module**: `app.services.queue`, `app.services.job_service`
- **Scope**: Queue abstraction interface, In-process concurrency-limited Asyncio worker pool, Job execution service, Session lifecycle.
- **Related Plan**: CHG-002 (WP-02, WP-06)
- **Status**: Approved for Implementation

---

## 1. Business Context & Objective

Việc tạo video giải thích hóa học bao gồm các tác vụ nặng: gọi LLM sinh kịch bản, sinh audio TTS đa phân đoạn, render hình ảnh slide độ phân giải cao và ghép video qua FFmpeg. Nếu chạy trực tiếp trên luồng HTTP hoặc khởi tạo task vô hạn qua `BackgroundTasks`, hệ thống sẽ nhanh chóng bị cạn kiệt CPU/RAM và sập server khi có nhiều người dùng gửi yêu cầu cùng lúc.

Để giải quyết triệt để:
1. Hệ thống áp dụng **Queue Abstraction** (`JobQueue`) giúp phân tách 100% tầng Web API khỏi Video Rendering Engine.
2. Cung cấp **In-Process Worker Pool** (`AsyncioWorkerQueue`) cho phép giới hạn số lượng video được render đồng thời (`MAX_CONCURRENT_JOBS`, mặc định = 2).
3. Đảm bảo sẵn sàng mở rộng sang Redis/Celery/ARQ phân tán trong tương lai chỉ bằng cách tráo đổi lớp triển khai của `JobQueue` mà không cần sửa bất kỳ dòng mã nào trong API hay Pipeline.

---

## 2. Technical Architecture & Component Design

```
                     ┌──────────────────────────────────────────┐
                     │            FastAPI Web Routes            │
                     │  POST /api/v1/jobs                       │
                     └─────────────────────┬────────────────────┘
                                           │
                                           │ await job_queue.enqueue(job_id)
                                           ▼
                     ┌──────────────────────────────────────────┐
                     │         JobQueue (Abstract Base)         │
                     │  + enqueue(job_id: str) -> None          │
                     └─────────────────────┬────────────────────┘
                                           │
                                           ▼
                     ┌──────────────────────────────────────────┐
                     │        AsyncioWorkerQueue (In-Memory)    │
                     │  - queue: asyncio.Queue[str]             │
                     │  - workers: list[asyncio.Task]           │
                     │  - concurrency: MAX_CONCURRENT_JOBS      │
                     └─────────────────────┬────────────────────┘
                                           │
                        ┌──────────────────┴──────────────────┐
                        ▼                                     ▼
             [Worker-0 Task Loop]                  [Worker-1 Task Loop]
             Pop job_id từ Queue                   Pop job_id từ Queue
                        │                                     │
                        └──────────────────┬──────────────────┘
                                           │
                                           ▼
                     ┌──────────────────────────────────────────┐
                     │       JobService.run_pipeline(job_id)    │
                     │  - async with async_session_factory()    │
                     │  - LangGraph StateGraph Execution        │
                     │  - Status Updates (generating/complete)  │
                     └──────────────────────────────────────────┘
```

---

## 3. Interface & Class Specifications (`app/services/queue.py`)

### 3.1 `JobQueue` (Abstract Base Class)
```python
from abc import ABC, abstractmethod

class JobQueue(ABC):
    @abstractmethod
    async def start(self) -> None:
        """Khởi động worker pool hoặc kết nối broker."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Dừng worker pool một cách an toàn (graceful shutdown)."""
        pass

    @abstractmethod
    async def enqueue(self, job_id: str) -> None:
        """Đưa job_id vào hàng đợi xử lý."""
        pass
```

### 3.2 `AsyncioWorkerQueue` (In-Process Concurrency Limited Implementation)
```python
import asyncio
import logging
from typing import Callable, Coroutine, Any

logger = logging.getLogger(__name__)

class AsyncioWorkerQueue(JobQueue):
    def __init__(
        self,
        worker_func: Callable[[str], Coroutine[Any, Any, None]],
        concurrency: int = 2
    ):
        self.worker_func = worker_func
        self.concurrency = concurrency
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self._workers: list[asyncio.Task] = []
        self._running: bool = False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        for i in range(self.concurrency):
            task = asyncio.create_task(self._worker_loop(f"video-worker-{i}"))
            self._workers.append(task)
        logger.info(f"AsyncioWorkerQueue started with {self.concurrency} concurrent workers.")

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        for task in self._workers:
            task.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info("AsyncioWorkerQueue stopped gracefully.")

    async def enqueue(self, job_id: str) -> None:
        await self.queue.put(job_id)
        logger.info(f"Job {job_id} enqueued. Queue size: {self.queue.qsize()}")

    async def _worker_loop(self, worker_name: str) -> None:
        while self._running:
            try:
                job_id = await self.queue.get()
                logger.info(f"[{worker_name}] Processing job {job_id}...")
                try:
                    await self.worker_func(job_id)
                except Exception as exc:
                    logger.error(f"[{worker_name}] Unhandled error processing job {job_id}: {exc}", exc_info=True)
                finally:
                    self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[{worker_name}] Worker loop error: {e}", exc_info=True)
```

---

## 4. Pipeline Execution Contract (`app/services/job_service.py`)

```python
async def run_pipeline(job_id: str) -> None:
    """
    Thực thi video generation pipeline cho một job_id cụ thể.
    Quản lý độc lập DB session để đảm bảo an toàn đa luồng/task.
    """
    async with async_session_factory() as session:
        repo = JobRepository(session)
        job = await repo.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found in database.")
            return

        # 1. Chuyển trạng thái sang generating
        await repo.update_status(job_id, JobStatus.generating)

        # 2. Khởi tạo StateGraph input state
        config_obj = VideoConfig(**job.config) if isinstance(job.config, dict) else VideoConfig()
        state: VideoGenerationState = {
            "job_id": job_id,
            "concept": job.concept,
            "config": config_obj,
            "retry_count": 0,
            "status": "generating"
        }

        try:
            # 3. Thực thi LangGraph pipeline
            final_state = await video_generation_graph.ainvoke(state)

            # 4. Kiểm tra kết quả
            if final_state.get("status") == "complete" and final_state.get("artifact_path"):
                await repo.update_status(
                    job_id,
                    JobStatus.complete,
                    artifact_path=final_state["artifact_path"],
                    retry_count=final_state.get("retry_count", 0)
                )
            else:
                await repo.update_status(
                    job_id,
                    JobStatus.failed,
                    error_reason=final_state.get("error_reason", "Pipeline finished with incomplete state"),
                    retry_count=final_state.get("retry_count", 0)
                )
        except Exception as exc:
            logger.error(f"Pipeline execution crashed for job {job_id}: {exc}", exc_info=True)
            await repo.update_status(
                job_id,
                JobStatus.failed,
                error_reason=f"Pipeline exception: {str(exc)}"
            )
```

---

## 5. Lifespan Integration (`app/main.py`)

Hàng đợi worker pool và kiểm tra stuck jobs được quản lý qua FastAPI `lifespan`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup:
    await create_tables()
    async with async_session_factory() as session:
        repo = JobRepository(session)
        await repo.reset_stuck_jobs()

    # Khởi động worker pool
    await app_queue.start()

    yield

    # Shutdown:
    await app_queue.stop()
```

---

## 6. Definition of Done (DoD)

1. [x] Lớp trừu tượng `JobQueue` và triển khai `AsyncioWorkerQueue` hoạt động đúng hợp đồng.
2. [x] Không bao giờ vượt quá `concurrency` (số worker song song tối đa) trong quá trình render.
3. [x] Tác vụ worker chạy hoàn toàn bất đồng bộ, phản hồi `POST /api/v1/jobs` ngay tức thì (< 50ms).
4. [x] Mọi ngoại lệ trong pipeline đều được bắt (catch) và cập nhật DB với `status="failed"` kèm `error_reason` rõ ràng.
5. [x] Khi ứng dụng shutdown, worker pool dừng mượt mà (graceful cancellation).

---

## 7. Verification Checklist & Unit Test Matrix

| ID | Test Case | Điều kiện thực hiện | Kết quả mong đợi |
|---|---|---|---|
| TC-02-01 | Enqueue và xử lý thành công | Enqueue 1 job_id vào `AsyncioWorkerQueue` | Worker gọi `worker_func(job_id)`, queue hoàn tất `task_done` |
| TC-02-02 | Kiểm soát Concurrency | Enqueue 5 jobs với `concurrency=2`, mỗi job sleep 0.2s | Tại mọi thời điểm số job đang chạy song song $\le 2$ |
| TC-02-03 | Xử lý ngoại lệ trong Worker | `worker_func` ném ngoại lệ bất kỳ | Worker không sập, bắt lỗi, ghi log, queue tiếp tục xử lý job kế |
| TC-02-04 | Dừng Worker Pool an toàn | Gọi `stop()` khi đang có job trong queue | Tất cả worker task bị cancel an toàn, không treo tiến trình |
| TC-02-05 | Quản lý DB Session trong Worker | Chạy `run_pipeline` trên mock DB | Session tự mở và đóng qua context manager, không rò rỉ session |
