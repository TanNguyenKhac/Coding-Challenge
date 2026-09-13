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
    target_duration_sec: int = Field(default=60, ge=15, le=300)
    target_audience: str = Field(default="high_school")
    aspect_ratio: str = Field(default="16:9")
    resolution: Tuple[int, int] = Field(default=(1280, 720))
    language: str = Field(default="vi")
    voice_gender: str = Field(default="neutral")


class JobCreate(BaseModel):
    concept: str = Field(..., min_length=3, max_length=500)
    config: Optional[VideoConfig] = Field(default_factory=VideoConfig)


class JobResponse(BaseModel):
    job_id: str
    concept: str
    config: VideoConfig
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    artifact_url: Optional[str] = None
    error_reason: Optional[str] = None

    model_config = {"from_attributes": True}
