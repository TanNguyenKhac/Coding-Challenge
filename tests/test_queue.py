import asyncio
from types import SimpleNamespace

import pytest

from app.models.job import JobStatus
from app.schemas.job import VideoConfig
from app.services.queue import AsyncioWorkerQueue


class TestAsyncioWorkerQueue:
    @pytest.mark.asyncio
    async def test_limits_concurrency_and_processes_all_jobs(self):
        configured = 2
        active = 0
        peak = 0
        completed = []

        async def worker(job_id: str) -> None:
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0.01)
            completed.append(job_id)
            active -= 1

        queue = AsyncioWorkerQueue(worker, concurrency=configured)
        await queue.start()
        await queue.start()
        try:
            for index in range(5):
                await queue.enqueue(f"job-{index}")
            await asyncio.wait_for(queue.queue.join(), timeout=1)
        finally:
            await queue.stop()

        assert sorted(completed) == [f"job-{index}" for index in range(5)]
        assert peak <= configured, (
            "SPEC-02 concurrency violation: "
            f"peak={peak}, configured={configured}; limit the worker pool"
        )
        assert len(queue._workers) == 0

    @pytest.mark.asyncio
    async def test_worker_error_does_not_stop_following_jobs(self):
        completed = []

        async def worker(job_id: str) -> None:
            if job_id == "bad-job":
                raise RuntimeError("controlled worker failure")
            completed.append(job_id)

        queue = AsyncioWorkerQueue(worker, concurrency=1)
        await queue.start()
        try:
            await queue.enqueue("bad-job")
            await queue.enqueue("good-job")
            await asyncio.wait_for(queue.queue.join(), timeout=1)
        finally:
            await queue.stop()

        assert completed == ["good-job"]

    @pytest.mark.asyncio
    async def test_stop_cancels_active_worker_without_hanging(self):
        started = asyncio.Event()
        cancelled = asyncio.Event()

        async def worker(job_id: str) -> None:
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

        queue = AsyncioWorkerQueue(worker, concurrency=1)
        await queue.start()
        await queue.enqueue("active-job")
        await asyncio.wait_for(started.wait(), timeout=1)

        await asyncio.wait_for(queue.stop(), timeout=1)

        assert cancelled.is_set()
        assert queue._workers == []


@pytest.mark.asyncio
async def test_run_pipeline_owns_and_closes_its_database_session(monkeypatch):
    from app.services import job_service

    session = object()
    session_events = []
    status_updates = []

    class SessionContext:
        async def __aenter__(self):
            session_events.append("enter")
            return session

        async def __aexit__(self, exc_type, exc, traceback):
            session_events.append("exit")

    class SessionFactory:
        def __call__(self):
            session_events.append("create")
            return SessionContext()

    class FakeRepository:
        def __init__(self, received_session):
            assert received_session is session

        async def get(self, job_id):
            return SimpleNamespace(
                job_id=job_id,
                concept="pH scale",
                config=VideoConfig().model_dump(),
            )

        async def update_status(self, job_id, status, **metadata):
            status_updates.append((job_id, status, metadata))

    class FakeGraph:
        async def ainvoke(self, state):
            return {
                **state,
                "status": "complete",
                "artifact_path": "artifacts/videos/job-1.mp4",
            }

    monkeypatch.setattr(job_service, "async_session_factory", SessionFactory())
    monkeypatch.setattr(job_service, "JobRepository", FakeRepository, raising=False)
    monkeypatch.setattr(job_service, "video_generation_graph", FakeGraph())

    await job_service.run_pipeline("job-1")

    assert session_events == ["create", "enter", "exit"], (
        "SPEC-01 session lifecycle violation: run_pipeline must enter and exit "
        "one worker-owned async_session_factory context"
    )
    assert [update[1] for update in status_updates] == [
        JobStatus.generating,
        JobStatus.complete,
    ]
    assert status_updates[-1][2]["artifact_path"] == "artifacts/videos/job-1.mp4"


@pytest.mark.asyncio
async def test_run_pipeline_persists_pipeline_exception_as_failed(monkeypatch):
    from app.services import job_service

    status_updates = []

    class SessionContext:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, exc_type, exc, traceback):
            return None

    class FakeRepository:
        def __init__(self, session):
            pass

        async def get(self, job_id):
            return SimpleNamespace(
                job_id=job_id,
                concept="covalent bonds",
                config=VideoConfig().model_dump(),
            )

        async def update_status(self, job_id, status, **metadata):
            status_updates.append((status, metadata))

    class FailingGraph:
        async def ainvoke(self, state):
            raise RuntimeError("controlled pipeline failure")

    monkeypatch.setattr(job_service, "async_session_factory", lambda: SessionContext())
    monkeypatch.setattr(job_service, "JobRepository", FakeRepository, raising=False)
    monkeypatch.setattr(job_service, "video_generation_graph", FailingGraph())

    await job_service.run_pipeline("job-2")

    assert [update[0] for update in status_updates] == [
        JobStatus.generating,
        JobStatus.failed,
    ]
    assert status_updates[-1][1]["error_reason"] == (
        "Pipeline exception: controlled pipeline failure"
    )


@pytest.mark.asyncio
async def test_lifespan_resets_stuck_jobs_and_manages_queue(monkeypatch):
    from app import main

    events = []

    async def fake_create_tables():
        events.append("create_tables")

    class SessionContext:
        async def __aenter__(self):
            events.append("session_enter")
            return object()

        async def __aexit__(self, exc_type, exc, traceback):
            events.append("session_exit")

    class FakeRepository:
        def __init__(self, session):
            pass

        async def reset_stuck_jobs(self):
            events.append("reset_stuck_jobs")

    class FakeQueue:
        async def start(self):
            events.append("queue_start")

        async def stop(self):
            events.append("queue_stop")

    monkeypatch.setattr(main, "create_tables", fake_create_tables, raising=False)
    monkeypatch.setattr(main, "async_session_factory", lambda: SessionContext(), raising=False)
    monkeypatch.setattr(main, "JobRepository", FakeRepository, raising=False)
    monkeypatch.setattr(main, "app_queue", FakeQueue(), raising=False)

    async with main.lifespan(main.app):
        events.append("serving")

    assert events == [
        "create_tables",
        "session_enter",
        "reset_stuck_jobs",
        "session_exit",
        "queue_start",
        "serving",
        "queue_stop",
    ]


def test_main_mounts_artifacts_at_public_path():
    from starlette.routing import Mount

    from app.config import settings
    from app.main import app, app_queue

    assert any(
        isinstance(route, Mount) and route.path == "/artifacts"
        for route in app.routes
    )
    assert settings.max_concurrent_jobs == 2
    assert app_queue.concurrency == settings.max_concurrent_jobs
