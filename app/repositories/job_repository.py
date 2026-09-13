import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus
from app.schemas.job import VideoConfig


class JobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, concept: str, config: dict | None = None) -> Job:
        if config is None:
            config = VideoConfig().model_dump()
        job = Job(
            job_id=str(uuid.uuid4()),
            concept=concept,
            config=config,
            status=JobStatus.pending,
        )
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get(self, job_id: str) -> Job | None:
        result = await self.session.execute(select(Job).where(Job.job_id == job_id))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Job]:
        result = await self.session.execute(select(Job).order_by(Job.created_at.desc()))
        return list(result.scalars().all())

    async def update_status(
        self,
        job_id: str,
        status: JobStatus,
        artifact_path: str | None = None,
        error_reason: str | None = None,
        retry_count: int | None = None,
    ) -> None:
        values: dict = {
            "status": status,
            "updated_at": datetime.now(timezone.utc),
        }
        if artifact_path is not None:
            values["artifact_path"] = artifact_path
        if error_reason is not None:
            values["error_reason"] = error_reason
        if retry_count is not None:
            values["retry_count"] = retry_count

        await self.session.execute(update(Job).where(Job.job_id == job_id).values(**values))
        await self.session.commit()

    async def reset_stuck_jobs(self) -> None:
        await self.session.execute(
            update(Job)
            .where(Job.status == JobStatus.generating)
            .values(
                status=JobStatus.failed,
                error_reason="server_restart",
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.session.commit()
