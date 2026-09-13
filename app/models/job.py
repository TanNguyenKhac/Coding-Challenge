import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, JSON, Enum as SAEnum, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class JobStatus(str, enum.Enum):
    pending = "pending"
    generating = "generating"
    complete = "complete"
    failed = "failed"


class Job(Base):
    __tablename__ = "jobs"

    job_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    concept: Mapped[str] = mapped_column(Text, nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[JobStatus] = mapped_column(SAEnum(JobStatus), nullable=False, default=JobStatus.pending)
    error_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    artifact_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
