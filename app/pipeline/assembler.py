import logging
import os
import subprocess
from abc import ABC, abstractmethod
from typing import List, Optional

from app.schemas.script import VideoScript

logger = logging.getLogger(__name__)


class VideoAssembler(ABC):
    """Abstract Base Class cho Media Assembler."""

    @abstractmethod
    async def assemble(
        self,
        job_id: str,
        script: VideoScript,
        audio_paths: List[str],
        slide_paths: List[str],
        output_dir: str,
    ) -> str:
        """Ghép audio và slide thành video MP4 hoàn chỉnh. Trả về đường dẫn file MP4."""
        pass


class MockAssembler(VideoAssembler):
    """Tạo file MP4 stub hợp lệ cho Unit Test mà không cần cài đặt FFmpeg."""

    async def assemble(
        self,
        job_id: str,
        script: VideoScript,
        audio_paths: List[str],
        slide_paths: List[str],
        output_dir: str,
    ) -> str:
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, f"{job_id}.mp4")
        # Ghi header MP4 tối giản hợp lệ (ftyp box)
        with open(out_path, "wb") as f:
            f.write(b"\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom")
        logger.info(f"[MockAssembler] Assembled stub video for job {job_id} at {out_path}")
        return out_path


class FFmpegAssembler(VideoAssembler):
    """Ghép video thực thụ bằng FFmpeg binary với cơ chế audio-visual duration sync."""

    async def assemble(
        self,
        job_id: str,
        script: VideoScript,
        audio_paths: List[str],
        slide_paths: List[str],
        output_dir: str,
    ) -> str:
        temp_dir = os.path.join(output_dir, "temp", job_id)
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        final_mp4 = os.path.join(output_dir, f"{job_id}.mp4")
        clip_paths = []

        logger.info(f"[FFmpegAssembler] Rendering {len(audio_paths)} chunk clips for job {job_id}")

        # 1. Render từng clip cho mỗi chunk (sync slide duration theo audio chunk)
        for i, (audio_p, slide_p) in enumerate(zip(audio_paths, slide_paths)):
            clip_p = os.path.join(temp_dir, f"clip_{i}.mp4")
            cmd = [
                "ffmpeg",
                "-y",
                "-loop", "1",
                "-i", slide_p,
                "-i", audio_p,
                "-c:v", "libx264",
                "-tune", "stillimage",
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                clip_p,
            ]
            logger.debug(f"[FFmpegAssembler] Running: {' '.join(cmd)}")
            res = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            clip_paths.append(clip_p)

        # 2. Nối các clips lại thành video hoàn chỉnh qua concat demuxer
        concat_list_file = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_list_file, "w", encoding="utf-8") as f:
            for cp in clip_paths:
                # Dùng forward slashes cho đường dẫn file trong concat list để tương thích Windows & POSIX
                normalized_path = os.path.abspath(cp).replace("\\", "/")
                f.write(f"file '{normalized_path}'\n")

        concat_cmd = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list_file,
            "-c", "copy",
            final_mp4,
        ]
        logger.debug(f"[FFmpegAssembler] Running concat: {' '.join(concat_cmd)}")
        subprocess.run(
            concat_cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        logger.info(f"[FFmpegAssembler] Successfully assembled final video for job {job_id} at {final_mp4}")
        return final_mp4
