import asyncio
import logging
import os
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

from app.pipeline.state import VideoGenerationState
from app.schemas.script import ScriptChunk

logger = logging.getLogger(__name__)


def render_single_slide(
    chunk: ScriptChunk,
    title: str,
    out_path: str,
    resolution: Tuple[int, int] = (1280, 720),
    chunk_index: int = 0,
) -> str:
    """Vẽ slide hình ảnh 1280x720 chuẩn bài giảng hóa học (Dark theme)."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    width, height = resolution
    img = Image.new("RGB", (width, height), color="#0F172A")  # Dark Slate Blue
    draw = ImageDraw.Draw(img)

    # 1. Header Bar
    draw.rectangle([(0, 0), (width, 80)], fill="#1E293B")
    draw.text((40, 25), f"🧪 CHEMISTRY: {title}", fill="#38BDF8")

    # 2. Chunk Section Heading
    heading_text = f"Section {chunk_index + 1}: {chunk.heading}"
    draw.text((60, 140), heading_text, fill="#F8FAFC")

    # 3. Visual & Formula Notes Box
    draw.rounded_rectangle(
        [(60, 240), (width - 60, height - 120)],
        radius=15,
        fill="#1E293B",
        outline="#475569",
        width=2,
    )
    draw.text((90, 280), "🔬 Visual Concepts & Key Notes:", fill="#94A3B8")
    draw.text((90, 340), f"• {chunk.visual_notes}", fill="#E2E8F0")
    narration_preview = chunk.narration[:120] + ("..." if len(chunk.narration) > 120 else "")
    draw.text((90, 420), f"• {narration_preview}", fill="#CBD5E1")

    # 4. Footer
    draw.text((60, height - 60), "Chemistry Video Engine — AI Generated Explanation", fill="#64748B")

    img.save(out_path)
    logger.debug(f"[slides_node] Rendered slide: {out_path}")
    return out_path


async def slides_node(state: VideoGenerationState) -> dict:
    """Render song song N slides qua asyncio.to_thread và asyncio.gather (Fan-out)."""
    script = state.get("script")
    if not script or not script.chunks:
        raise ValueError("Cannot render slides: script has no chunks.")

    job_id = state["job_id"]
    config = state.get("config")
    resolution = config.resolution if config and hasattr(config, "resolution") else (1280, 720)

    temp_dir = os.path.join("./artifacts", "temp", job_id)
    os.makedirs(temp_dir, exist_ok=True)

    tasks = []
    for i, chunk in enumerate(script.chunks):
        chunk_id = getattr(chunk, "chunk_id", None)
        idx = i if chunk_id is None else chunk_id
        slide_file = os.path.join(temp_dir, f"slide_{idx}.png")
        tasks.append(
            asyncio.to_thread(
                render_single_slide,
                chunk,
                script.title,
                slide_file,
                resolution,
                i,
            )
        )

    slide_paths: List[str] = await asyncio.gather(*tasks)
    logger.info(f"[slides_node] Rendered {len(slide_paths)} slides for job {job_id}")
    return {"slide_paths": list(slide_paths)}
