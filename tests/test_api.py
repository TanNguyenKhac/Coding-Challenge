import pytest
import pytest_asyncio
from app.repositories.job_repository import JobRepository
from app.models.job import JobStatus
from app.schemas.job import VideoConfig


class TestJobRepository:
    @pytest.mark.asyncio
    async def test_create_job(self, db_session, sample_config):
        repo = JobRepository(db_session)
        job = await repo.create("How does the pH scale work?", sample_config)

        assert job.job_id is not None
        assert len(job.job_id) == 36  # UUID format
        assert job.concept == "How does the pH scale work?"
        assert job.status == JobStatus.pending
        assert job.retry_count == 0
        assert job.error_reason is None

    @pytest.mark.asyncio
    async def test_create_job_default_config(self, db_session):
        repo = JobRepository(db_session)
        job = await repo.create("Covalent bonds explained")

        assert job.config is not None
        assert job.config["target_duration_sec"] == 60

    @pytest.mark.asyncio
    async def test_get_job(self, db_session, sample_config):
        repo = JobRepository(db_session)
        created = await repo.create("Test concept", sample_config)

        fetched = await repo.get(created.job_id)
        assert fetched is not None
        assert fetched.job_id == created.job_id
        assert fetched.concept == "Test concept"

    @pytest.mark.asyncio
    async def test_get_job_not_found(self, db_session):
        repo = JobRepository(db_session)
        result = await repo.get("00000000-0000-0000-0000-000000000000")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all(self, db_session, sample_config):
        repo = JobRepository(db_session)
        await repo.create("Concept A", sample_config)
        await repo.create("Concept B", sample_config)

        jobs = await repo.list_all()
        assert len(jobs) >= 2
        # Most recent first
        assert jobs[0].created_at >= jobs[1].created_at

    @pytest.mark.asyncio
    async def test_update_status_to_generating(self, db_session, sample_config):
        repo = JobRepository(db_session)
        job = await repo.create("Test", sample_config)

        await repo.update_status(job.job_id, JobStatus.generating)
        updated = await repo.get(job.job_id)
        assert updated.status == JobStatus.generating

    @pytest.mark.asyncio
    async def test_update_status_to_complete_with_artifact(self, db_session, sample_config):
        repo = JobRepository(db_session)
        job = await repo.create("Test", sample_config)

        await repo.update_status(job.job_id, JobStatus.complete, artifact_path="/artifacts/test.mp4")
        updated = await repo.get(job.job_id)
        assert updated.status == JobStatus.complete
        assert updated.artifact_path == "/artifacts/test.mp4"

    @pytest.mark.asyncio
    async def test_update_status_to_failed(self, db_session, sample_config):
        repo = JobRepository(db_session)
        job = await repo.create("Test", sample_config)

        await repo.update_status(job.job_id, JobStatus.failed, error_reason="LLM error")
        updated = await repo.get(job.job_id)
        assert updated.status == JobStatus.failed
        assert updated.error_reason == "LLM error"

    @pytest.mark.asyncio
    async def test_reset_stuck_jobs(self, db_session, sample_config):
        repo = JobRepository(db_session)
        job = await repo.create("Stuck job", sample_config)
        await repo.update_status(job.job_id, JobStatus.generating)

        await repo.reset_stuck_jobs()

        reset = await repo.get(job.job_id)
        assert reset.status == JobStatus.failed
        assert reset.error_reason == "server_restart"


class RecordingQueue:
    def __init__(self):
        self.job_ids = []

    async def enqueue(self, job_id):
        self.job_ids.append(job_id)


@pytest_asyncio.fixture
async def api_client(db_session):
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from app.api.v1.jobs import router
    from app.database import get_session

    api = FastAPI()
    queue = RecordingQueue()
    api.state.job_queue = queue
    api.include_router(router, prefix="/api/v1")

    async def override_session():
        yield db_session

    api.dependency_overrides[get_session] = override_session
    transport = ASGITransport(app=api)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, queue


class TestJobsAPI:
    @pytest.mark.asyncio
    async def test_create_list_and_get_job(self, api_client):
        from time import perf_counter

        client, queue = api_client

        started = perf_counter()
        created = await client.post(
            "/api/v1/jobs",
            json={
                "concept": "How does the pH scale work?",
                "config": {"target_duration_sec": 60},
            },
        )
        elapsed = perf_counter() - started

        assert created.status_code == 201
        assert elapsed < 0.05
        body = created.json()
        assert body["status"] == "pending"
        assert body["config"]["target_duration_sec"] == 60
        assert body["artifact_url"] is None
        assert queue.job_ids == [body["job_id"]]

        listed = await client.get("/api/v1/jobs")
        assert listed.status_code == 200
        assert [job["job_id"] for job in listed.json()] == [body["job_id"]]

        detail = await client.get(f"/api/v1/jobs/{body['job_id']}")
        assert detail.status_code == 200
        assert detail.json()["concept"] == "How does the pH scale work?"

    @pytest.mark.asyncio
    async def test_validation_rejects_before_write_or_enqueue(self, api_client):
        client, queue = api_client

        response = await client.post("/api/v1/jobs", json={"concept": "ab"})

        assert response.status_code == 422
        assert queue.job_ids == []
        listed = await client.get("/api/v1/jobs")
        assert listed.json() == []

    @pytest.mark.asyncio
    async def test_not_found_error_contract(self, api_client):
        client, _ = api_client
        unknown_id = "00000000-0000-0000-0000-000000000000"

        detail = await client.get(f"/api/v1/jobs/{unknown_id}")
        artifact = await client.get(f"/api/v1/jobs/{unknown_id}/artifact")

        assert detail.status_code == 404
        assert detail.json() == {"detail": "Job not found"}
        assert artifact.status_code == 404
        assert artifact.json() == {"detail": "Job or artifact file not found"}

    @pytest.mark.asyncio
    async def test_artifact_status_detail_and_file_contract(
        self, api_client, db_session, tmp_path
    ):
        client, _ = api_client
        created = await client.post(
            "/api/v1/jobs", json={"concept": "Ionic versus covalent bonding"}
        )
        job_id = created.json()["job_id"]

        pending = await client.get(f"/api/v1/jobs/{job_id}/artifact")
        assert pending.status_code == 400
        assert pending.json() == {
            "detail": "Job is not complete yet (status: pending)"
        }

        artifact_path = tmp_path / f"{job_id}.mp4"
        artifact_path.write_bytes(b"deterministic-mp4-stub")
        repo = JobRepository(db_session)
        await repo.update_status(
            job_id,
            JobStatus.complete,
            artifact_path=str(artifact_path),
        )

        detail = await client.get(f"/api/v1/jobs/{job_id}")
        assert detail.status_code == 200
        assert detail.json()["status"] == "complete"
        assert detail.json()["artifact_url"] == f"/artifacts/{job_id}.mp4"

        artifact = await client.get(f"/api/v1/jobs/{job_id}/artifact")
        assert artifact.status_code == 200
        assert artifact.headers["content-type"] == "video/mp4"
        assert artifact.content == b"deterministic-mp4-stub"

    @pytest.mark.asyncio
    async def test_complete_job_with_missing_file_returns_404(
        self, api_client, db_session, tmp_path
    ):
        client, _ = api_client
        created = await client.post(
            "/api/v1/jobs", json={"concept": "Covalent bonds explained"}
        )
        job_id = created.json()["job_id"]
        repo = JobRepository(db_session)
        await repo.update_status(
            job_id,
            JobStatus.complete,
            artifact_path=str(tmp_path / "missing.mp4"),
        )

        response = await client.get(f"/api/v1/jobs/{job_id}/artifact")

        assert response.status_code == 404
        assert response.json() == {"detail": "Job or artifact file not found"}
