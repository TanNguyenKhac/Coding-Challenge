from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.jobs import router as jobs_router
from app.config import settings
from app.database import async_session_factory, create_tables
from app.repositories.job_repository import JobRepository
from app.services.job_service import run_pipeline
from app.services.queue import AsyncioWorkerQueue


app_queue = AsyncioWorkerQueue(
    run_pipeline,
    concurrency=settings.max_concurrent_jobs,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    async with async_session_factory() as session:
        await JobRepository(session).reset_stuck_jobs()

    app.state.job_queue = app_queue
    await app_queue.start()
    try:
        yield
    finally:
        await app_queue.stop()


app = FastAPI(lifespan=lifespan)
app.state.job_queue = app_queue
app.include_router(jobs_router, prefix="/api/v1")
app.mount(
    "/artifacts",
    StaticFiles(directory=settings.artifacts_dir, check_dir=False),
    name="artifacts",
)
