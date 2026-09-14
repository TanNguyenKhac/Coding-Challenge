import logging

from app.database import async_session_factory
from app.models.job import JobStatus
from app.pipeline.graph import build_video_graph
from app.pipeline.state import VideoGenerationState
from app.repositories.job_repository import JobRepository
from app.schemas.job import VideoConfig


logger = logging.getLogger(__name__)
video_generation_graph = build_video_graph()


async def run_pipeline(job_id: str) -> None:
    async with async_session_factory() as session:
        repository = JobRepository(session)
        job = await repository.get(job_id)
        if job is None:
            logger.error("Job %s not found in database", job_id)
            return

        await repository.update_status(job_id, JobStatus.generating)
        config = (
            VideoConfig(**job.config)
            if isinstance(job.config, dict)
            else VideoConfig()
        )
        state: VideoGenerationState = {
            "job_id": job_id,
            "concept": job.concept,
            "config": config,
            "retry_count": 0,
            "status": "generating",
        }

        try:
            final_state = await video_generation_graph.ainvoke(state)
            retry_count = final_state.get("retry_count", 0)
            artifact_path = final_state.get("artifact_path")
            if final_state.get("status") == "complete" and artifact_path:
                await repository.update_status(
                    job_id,
                    JobStatus.complete,
                    artifact_path=artifact_path,
                    retry_count=retry_count,
                )
                return

            await repository.update_status(
                job_id,
                JobStatus.failed,
                error_reason=final_state.get(
                    "error_reason",
                    "Pipeline finished with incomplete state",
                ),
                retry_count=retry_count,
            )
        except Exception as exc:
            logger.exception("Pipeline execution crashed for job %s", job_id)
            await repository.update_status(
                job_id,
                JobStatus.failed,
                error_reason=f"Pipeline exception: {exc}",
            )
