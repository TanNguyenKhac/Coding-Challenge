# Functional Specification: SPEC-04 — Media Generation & Parallel Chunk Assembly

- **Module**: `app.pipeline.assembler`, `app.pipeline.nodes.audio_node`, `app.pipeline.nodes.slides_node`, `app.pipeline.nodes.assembler_node`
- **Scope**: Parallel chunk TTS audio generation, Parallel chunk slide image rendering, FFmpeg video assembly with audio-visual duration synchronization, MockAssembler for tests.
- **Related Plan**: CHG-002 (WP-01, WP-05)
- **Status**: Approved for Implementation

---

## 1. Business Context & Objective

Một video giáo dục hóa học cần kết hợp nhuần nhuyễn giữa **hình ảnh trực quan** (công thức hóa học, tiêu đề, ghi chú phân tử) và **lời thuyết minh âm thanh** (audio narration).

**Mục tiêu kỹ thuật:**
1. **Parallel Chunk Generation (Fan-out)**: Xử lý song song $N$ phân đoạn audio và $N$ slide ảnh qua `asyncio.gather` để giảm thiểu thời gian chờ đợi.
2. **Audio-Visual Duration Synchronization**: Mỗi slide ảnh tĩnh phải hiển thị đúng bằng thời lượng file audio của phân đoạn đó, đảm bảo lời đọc và hình ảnh luôn ăn khớp 100%.
3. **Zero-Cost & Offline Fallback**: Sử dụng Pillow (đồ họa local) và gTTS (Google TTS miễn phí) với fallback sang `pyttsx3` (TTS offline cục bộ) khi mất mạng hoặc bị rate-limit.
4. **Mock Assembler**: Cung cấp `MockAssembler` phục vụ unit test nhanh chóng mà không cần cài đặt FFmpeg binary trên môi trường CI/test.

---

## 2. Technical Architecture & Media Processing Flow

```
   [VideoScript: Chunk 0, Chunk 1, Chunk 2]
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
[Parallel Audio Worker]     [Parallel Slide Worker]
(gTTS + pyttsx3 fallback)   (Pillow 1280x720 Dark Theme)
 ├── audio_chunk_0.mp3       ├── slide_chunk_0.png
 ├── audio_chunk_1.mp3       ├── slide_chunk_1.png
 └── audio_chunk_2.mp3       └── slide_chunk_2.png
        └─────────────┬─────────────┘
                      │ (Fan-in: Barrier Synchronization)
                      ▼
         [VideoAssembler.assemble()]
  - Đo thời lượng audio_chunk_i.mp3 (T_i seconds)
  - Ghép slide_chunk_i.png + audio_chunk_i.mp3 -> clip_i.mp4 (duration = T_i)
  - Nối (concat) các clip_i.mp4 -> final artifact: artifacts/{job_id}.mp4
```

---

## 3. Class & Interface Specifications

### 3.1 VideoAssembler Interface & Implementations (`app/pipeline/assembler.py`)

```python
from abc import ABC, abstractmethod
import os
import subprocess
from app.schemas.script import VideoScript

class VideoAssembler(ABC):
    @abstractmethod
    async def assemble(
        self,
        job_id: str,
        script: VideoScript,
        audio_paths: list[str],
        slide_paths: list[str],
        output_dir: str
    ) -> str:
        """Ghép audio và slide thành video MP4 hoàn chỉnh. Trả về đường dẫn file MP4."""
        pass

class MockAssembler(VideoAssembler):
    """Tạo file MP4 stub hợp lệ cho Unit Test mà không cần FFmpeg."""
    async def assemble(
        self,
        job_id: str,
        script: VideoScript,
        audio_paths: list[str],
        slide_paths: list[str],
        output_dir: str
    ) -> str:
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, f"{job_id}.mp4")
        # Ghi header MP4 tối giản hợp lệ
        with open(out_path, "wb") as f:
            f.write(b"\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom")
        return out_path

class FFmpegAssembler(VideoAssembler):
    """Ghép video thực thụ bằng FFmpeg binary."""
    async def assemble(
        self,
        job_id: str,
        script: VideoScript,
        audio_paths: list[str],
        slide_paths: list[str],
        output_dir: str
    ) -> str:
        # 1. Tạo thư mục tạm cho job
        temp_dir = os.path.join(output_dir, "temp", job_id)
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        final_mp4 = os.path.join(output_dir, f"{job_id}.mp4")
        clip_paths = []

        # 2. Render từng clip cho mỗi chunk (sync audio duration)
        for i, (audio_p, slide_p) in enumerate(zip(audio_paths, slide_paths)):
            clip_p = os.path.join(temp_dir, f"clip_{i}.mp4")
            # Lệnh FFmpeg: loop image tĩnh với audio, dừng khi hết audio (-shortest)
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", slide_p,
                "-i", audio_p,
                "-c:v", "libx264", "-tune", "stillimage",
                "-c:a", "aac", "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                clip_p
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            clip_paths.append(clip_p)

        # 3. Nối các clips lại thành video hoàn chỉnh qua concat demuxer
        concat_list_file = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_list_file, "w", encoding="utf-8") as f:
            for cp in clip_paths:
                f.write(f"file '{os.path.abspath(cp)}'\n")

        concat_cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_list_file,
            "-c", "copy",
            final_mp4
        ]
        subprocess.run(concat_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return final_mp4
```

---

## 4. Pipeline Nodes Specification

### 4.1 Parallel Audio Node (`app/pipeline/nodes/audio_node.py`)

```python
import asyncio
import os
import logging
from gtts import gTTS
import pyttsx3
from app.pipeline.state import VideoGenerationState
from app.schemas.script import ScriptChunk

logger = logging.getLogger(__name__)

def generate_single_audio(chunk: ScriptChunk, out_path: str, lang: str = "vi") -> str:
    """Sinh audio TTS cho một chunk với fallback pyttsx3."""
    try:
        tts = gTTS(text=chunk.narration, lang=lang, slow=False)
        tts.save(out_path)
    except Exception as gtts_err:
        logger.warning(f"gTTS failed for chunk {chunk.chunk_id}, falling back to pyttsx3: {gtts_err}")
        engine = pyttsx3.init()
        engine.save_to_file(chunk.narration, out_path)
        engine.runAndWait()
    return out_path

async def audio_node(state: VideoGenerationState) -> dict:
    """Xử lý song song N chunks qua asyncio.to_thread / gather."""
    script = state["script"]
    job_id = state["job_id"]
    lang = state.get("config").language if state.get("config") else "vi"
    
    temp_dir = os.path.join("./artifacts", "temp", job_id)
    os.makedirs(temp_dir, exist_ok=True)

    tasks = []
    for chunk in script.chunks:
        audio_file = os.path.join(temp_dir, f"audio_{chunk.chunk_id}.mp3")
        tasks.append(asyncio.to_thread(generate_single_audio, chunk, audio_file, lang))

    audio_paths = await asyncio.gather(*tasks)
    return {"audio_paths": list(audio_paths)}
```

---

### 4.2 Parallel Slides Node (`app/pipeline/nodes/slides_node.py`)

```python
import asyncio
import os
from PIL import Image, ImageDraw, ImageFont
from app.pipeline.state import VideoGenerationState
from app.schemas.script import ScriptChunk

def render_single_slide(chunk: ScriptChunk, title: str, out_path: str, resolution=(1280, 720)) -> str:
    """Vẽ slide hình ảnh 1280x720 chuẩn bài giảng hóa học (Dark theme)."""
    width, height = resolution
    img = Image.new("RGB", (width, height), color="#0F172A")  # Dark Slate Blue
    draw = ImageDraw.Draw(img)

    # 1. Header Bar
    draw.rectangle([(0, 0), (width, 80)], fill="#1E293B")
    draw.text((40, 25), f"🧪 CHEMISTRY: {title}", fill="#38BDF8")

    # 2. Chunk Section Heading
    draw.text((60, 140), f"Section {chunk.chunk_id + 1}: {chunk.heading}", fill="#F8FAFC")

    # 3. Visual & Formula Notes Box
    draw.rounded_rectangle([(60, 240), (width - 60, height - 120)], radius=15, fill="#1E293B", outline="#475569", width=2)
    draw.text((90, 280), "🔬 Visual Concepts & Key Notes:", fill="#94A3B8")
    draw.text((90, 340), f"• {chunk.visual_notes}", fill="#E2E8F0")
    draw.text((90, 420), f"• {chunk.narration[:120]}...", fill="#CBD5E1")

    # 4. Footer
    draw.text((60, height - 60), "Chemistry Video Engine — AI Generated Explanation", fill="#64748B")

    img.save(out_path)
    return out_path

async def slides_node(state: VideoGenerationState) -> dict:
    """Render song song N slides qua asyncio.gather."""
    script = state["script"]
    job_id = state["job_id"]
    resolution = state.get("config").resolution if state.get("config") else (1280, 720)

    temp_dir = os.path.join("./artifacts", "temp", job_id)
    os.makedirs(temp_dir, exist_ok=True)

    tasks = []
    for chunk in script.chunks:
        slide_file = os.path.join(temp_dir, f"slide_{chunk.chunk_id}.png")
        tasks.append(asyncio.to_thread(render_single_slide, chunk, script.title, slide_file, resolution))

    slide_paths = await asyncio.gather(*tasks)
    return {"slide_paths": list(slide_paths)}
```

---

### 4.3 Assembler Node (`app/pipeline/nodes/assembler_node.py`)

```python
from app.pipeline.state import VideoGenerationState
from app.pipeline.assembler import VideoAssembler

async def assembler_node(state: VideoGenerationState, assembler: VideoAssembler) -> dict:
    """Gọi assembler để ghép audio và slides thành file MP4 hoàn chỉnh."""
    job_id = state["job_id"]
    script = state["script"]
    audio_paths = state["audio_paths"]
    slide_paths = state["slide_paths"]
    output_dir = "./artifacts/videos"

    artifact_path = await assembler.assemble(job_id, script, audio_paths, slide_paths, output_dir)
    return {
        "artifact_path": artifact_path,
        "status": "complete"
    }
```

---

## 5. Definition of Done (DoD)

1. [x] Audio generation chạy song song cho tất cả các chunks, tự động fallback sang pyttsx3 nếu gTTS gặp sự cố.
2. [x] Slides generation tạo ra hình ảnh 1280×720 sắc nét, bố cục dark theme sư phạm rõ ràng với tiêu đề và ghi chú trực quan.
3. [x] `FFmpegAssembler` tạo file MP4 đồng bộ hoàn hảo giữa thời lượng hiển thị slide và độ dài âm thanh thuyết minh từng chunk.
4. [x] `MockAssembler` tạo file MP4 stub hợp lệ cho unit test với thời gian thực thi < 50ms.
5. [x] File MP4 cuối cùng lưu tại `artifacts/videos/{job_id}.mp4` và phát được trên các trình phát đa phương tiện tiêu chuẩn.

---

## 6. Verification Checklist & Unit Test Matrix

| ID | Test Case | Kịch bản kiểm thử | Kết quả mong đợi |
|---|---|---|---|
| TC-04-01 | Render Mock Assembler | Gọi `MockAssembler.assemble()` với danh sách paths giả lập | Tạo file `.mp4` không rỗng tại đường dẫn chỉ định |
| TC-04-02 | Parallel Audio Node | Gọi `audio_node` với script có 3 chunks | Tạo đủ 3 file `audio_0.mp3`, `audio_1.mp3`, `audio_2.mp3` |
| TC-04-03 | Parallel Slides Node | Gọi `slides_node` với script có 3 chunks | Tạo đủ 3 file PNG kích thước 1280x720 |
| TC-04-04 | FFmpeg Duration Sync | Gọi `FFmpegAssembler` với audio và slide thật | Video đầu ra có tổng thời lượng bằng tổng thời lượng các file audio |
| TC-04-05 | Full Assembler Node Integration | Gọi `assembler_node` trong StateGraph với `MockAssembler` | State trả về `status: "complete"` và `artifact_path` chính xác |
