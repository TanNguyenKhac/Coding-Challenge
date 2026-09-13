from typing import Optional

from pydantic import BaseModel, Field


class ScriptChunk(BaseModel):
    chunk_id: int = Field(description="Zero-based scene index")
    heading: str = Field(
        min_length=2,
        description="Visual heading shown on the scene slide",
    )
    narration: str = Field(
        min_length=10,
        description="Detailed narration passed to text-to-speech",
    )
    visual_notes: str = Field(
        min_length=5,
        description="Chemical formula, symbol, or molecular structure to visualize",
    )
    duration_hint_sec: Optional[int] = Field(
        default=None,
        description="Suggested scene duration in seconds",
    )


class VideoScript(BaseModel):
    title: str = Field(
        min_length=3,
        description="Main title of the chemistry lesson",
    )
    summary: str = Field(
        min_length=10,
        description="One- or two-sentence lesson summary",
    )
    chunks: list[ScriptChunk] = Field(
        min_length=3,
        description="At least three pedagogical lesson scenes",
    )
