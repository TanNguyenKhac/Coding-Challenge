import logging
import os
from typing import Optional

from app.config import settings
from app.pipeline.assembler import FFmpegAssembler, VideoAssembler
from app.pipeline.state import VideoGenerationState

logger = logging.getLogger(__name__)


async def assembler_node(
    state: VideoGenerationState,
    assembler: Optional[VideoAssembler] = None,
) -> dict:
    """Gọi assembler để ghép audio và slides thành file MP4 hoàn chỉnh."""
    job_id = state["job_id"]
    script = state.get("script")
    audio_paths = state.get("audio_paths", [])
    slide_paths = state.get("slide_paths", [])
    output_dir = settings.artifacts_dir or "./artifacts/videos"

    if assembler is None:
        assembler = FFmpegAssembler()

    logger.info(
        f"[assembler_node] Assembling video for job_id={job_id} using {assembler.__class__.__name__}"
    )

    artifact_path = await assembler.assemble(
        job_id=job_id,
        script=script,
        audio_paths=audio_paths,
        slide_paths=slide_paths,
        output_dir=output_dir,
    )

    return {
        "artifact_path": artifact_path,
        "status": "complete",
    }
