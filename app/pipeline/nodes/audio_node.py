import asyncio
import logging
import os
from typing import List

from gtts import gTTS
import pyttsx3

from app.pipeline.state import VideoGenerationState
from app.schemas.script import ScriptChunk

logger = logging.getLogger(__name__)


def generate_single_audio(chunk: ScriptChunk, out_path: str, lang: str = "vi") -> str:
    """Sinh audio TTS cho một chunk kịch bản với cơ chế tự động fallback sang pyttsx3."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    try:
        tts = gTTS(text=chunk.narration, lang=lang, slow=False)
        tts.save(out_path)
        logger.debug(f"[audio_node] Generated gTTS audio: {out_path}")
    except Exception as gtts_err:
        chunk_idx = getattr(chunk, "chunk_id", None)
        logger.warning(
            f"[audio_node] gTTS failed for chunk {chunk_idx}, falling back to pyttsx3: {gtts_err}"
        )
        try:
            engine = pyttsx3.init()
            engine.save_to_file(chunk.narration, out_path)
            engine.runAndWait()
            logger.debug(f"[audio_node] Generated pyttsx3 fallback audio: {out_path}")
        except Exception as pyttsx_err:
            logger.error(f"[audio_node] pyttsx3 fallback also failed: {pyttsx_err}")
            raise
    return out_path


async def audio_node(state: VideoGenerationState) -> dict:
    """Xử lý song song N chunks qua asyncio.to_thread và asyncio.gather (Fan-out)."""
    script = state.get("script")
    if not script or not script.chunks:
        raise ValueError("Cannot generate audio: script has no chunks.")

    job_id = state["job_id"]
    config = state.get("config")
    lang = config.language if config and hasattr(config, "language") else "vi"

    temp_dir = os.path.join("./artifacts", "temp", job_id)
    os.makedirs(temp_dir, exist_ok=True)

    tasks = []
    for i, chunk in enumerate(script.chunks):
        chunk_id = getattr(chunk, "chunk_id", None)
        idx = i if chunk_id is None else chunk_id
        audio_file = os.path.join(temp_dir, f"audio_{idx}.mp3")
        tasks.append(asyncio.to_thread(generate_single_audio, chunk, audio_file, lang))

    audio_paths: List[str] = await asyncio.gather(*tasks)
    logger.info(f"[audio_node] Generated {len(audio_paths)} audio chunks for job {job_id}")
    return {"audio_paths": list(audio_paths)}
