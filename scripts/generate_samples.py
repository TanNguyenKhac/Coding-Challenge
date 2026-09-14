"""Generate 3 sample MP4 videos and save to artifacts/samples/.

Submits the 3 required chemistry questions to the running API server,
waits for completion, downloads the artifacts, and writes them to
fixed filenames under artifacts/samples/.  Also generates a README.md
with metadata about each sample.
"""

import asyncio
import os
import sys
import time
from pathlib import Path

import httpx

REQUIRED_CONCEPTS = [
    ("How does the pH scale work?", "job-ph-scale.mp4"),
    ("Why do atoms form covalent bonds?", "job-covalent-bonds.mp4"),
    ("What is the difference between ionic and covalent bonding?", "job-ionic-vs-covalent.mp4"),
]

BASE_URL = "http://127.0.0.1:8000/api/v1"
SAMPLES_DIR = Path("artifacts/samples")
POLL_INTERVAL = 2
TIMEOUT_SECONDS = 120


async def generate_and_download(
    client: httpx.AsyncClient, concept: str, filename: str,
) -> dict:
    print(f"\n[+] Submitting: '{concept}'")
    resp = await client.post(f"{BASE_URL}/jobs", json={"concept": concept})
    assert resp.status_code == 201, f"Create failed: {resp.text}"
    job_id = resp.json()["job_id"]
    print(f"    Job ID: {job_id}")

    start_time = time.time()
    while time.time() - start_time < TIMEOUT_SECONDS:
        await asyncio.sleep(POLL_INTERVAL)
        status_resp = await client.get(f"{BASE_URL}/jobs/{job_id}")
        data = status_resp.json()
        status = data["status"]
        elapsed = int(time.time() - start_time)
        print(f"    Polling: {status} ({elapsed}s)")
        if status == "complete":
            art_resp = await client.get(f"{BASE_URL}/jobs/{job_id}/artifact")
            assert art_resp.status_code == 200
            out_path = SAMPLES_DIR / filename
            out_path.write_bytes(art_resp.content)
            size_kb = len(art_resp.content) / 1024
            print(f"    [SAVED] {out_path} ({size_kb:.1f} KB)")
            return {
                "filename": filename,
                "concept": concept,
                "job_id": job_id,
                "size_bytes": len(art_resp.content),
            }
        elif status == "failed":
            raise RuntimeError(
                f"Job {job_id} failed: {data.get('error_reason')}"
            )

    raise TimeoutError(f"Job {job_id} timed out after {TIMEOUT_SECONDS}s")


def write_readme(samples: list[dict]) -> None:
    lines = [
        "# Sample Videos",
        "",
        "Pre-generated chemistry explanation videos for quick quality review.",
        "",
        "## Samples",
        "",
        "| File | Concept | Size |",
        "|------|---------|------|",
    ]
    for s in samples:
        size_str = f"{s['size_bytes'] / 1024:.1f} KB"
        lines.append(f"| `{s['filename']}` | {s['concept']} | {size_str} |")

    lines += [
        "",
        "## Technical Specs",
        "",
        "- Resolution: 1280x720 (16:9)",
        "- Video codec: H.264 (when FFmpeg available) / minimal ftyp header (MockAssembler)",
        "- Audio: gTTS MP3 per chunk",
        "- Target audience: high_school",
        "- Language: vi",
        "",
        "## Regeneration",
        "",
        "```bash",
        "# Start server first",
        "uvicorn app.main:app --host 127.0.0.1 --port 8000",
        "",
        "# Generate samples",
        "python scripts/generate_samples.py",
        "```",
    ]
    readme_path = SAMPLES_DIR / "README.md"
    readme_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[+] README written to {readme_path}")


async def main() -> None:
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    print("=== GENERATING SAMPLE VIDEOS ===")
    samples = []
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS + 10) as client:
        for concept, filename in REQUIRED_CONCEPTS:
            info = await generate_and_download(client, concept, filename)
            samples.append(info)
    write_readme(samples)
    print("\n=== ALL 3 SAMPLE VIDEOS GENERATED SUCCESSFULLY ===")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (AssertionError, RuntimeError, TimeoutError) as exc:
        print(f"\n[FAIL] Sample generation failed: {exc}", file=sys.stderr)
        sys.exit(1)
