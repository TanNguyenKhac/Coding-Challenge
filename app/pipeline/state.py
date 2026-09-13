from typing import NotRequired, TypedDict

from app.schemas.script import VideoScript
from app.schemas.job import VideoConfig


class VideoGenerationState(TypedDict):
    job_id: str
    concept: str
    config: VideoConfig
    retry_count: int
    status: str
    script: NotRequired[VideoScript | None]
    error_reason: NotRequired[str | None]
    audio_paths: NotRequired[list[str]]
    slide_paths: NotRequired[list[str]]
    artifact_path: NotRequired[str | None]
