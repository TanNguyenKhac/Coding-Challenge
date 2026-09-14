from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.job import Job, JobStatus
from app.repositories.job_repository import JobRepository
from app.schemas.job import JobCreate, JobResponse, VideoConfig
from app.services.queue import JobQueue


router = APIRouter()


def _response_for(job: Job) -> JobResponse:
    artifact_url = None
    if job.status == JobStatus.complete:
        artifact_url = f"/artifacts/{job.job_id}.mp4"
    response = JobResponse.model_validate(job)
    return response.model_copy(update={"artifact_url": artifact_url})


def _job_queue(request: Request) -> JobQueue:
    return request.app.state.job_queue


@router.post(
    "/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_job(
    payload: JobCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> JobResponse:
    repository = JobRepository(session)
    config = payload.config or VideoConfig()
    job = await repository.create(payload.concept, config.model_dump())
    await _job_queue(request).enqueue(job.job_id)
    return _response_for(job)


@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(
    session: AsyncSession = Depends(get_session),
) -> list[JobResponse]:
    repository = JobRepository(session)
    return [_response_for(job) for job in await repository.list_all()]


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    session: AsyncSession = Depends(get_session),
) -> JobResponse:
    repository = JobRepository(session)
    job = await repository.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return _response_for(job)


@router.get("/jobs/{job_id}/artifact", response_class=FileResponse)
async def get_job_artifact(
    job_id: str,
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    repository = JobRepository(session)
    job = await repository.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job or artifact file not found",
        )
    if job.status != JobStatus.complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not complete yet (status: {job.status.value})",
        )
    if not job.artifact_path or not Path(job.artifact_path).is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job or artifact file not found",
        )

    return FileResponse(
        job.artifact_path,
        media_type="video/mp4",
        filename=f"job_{job_id}.mp4",
    )
