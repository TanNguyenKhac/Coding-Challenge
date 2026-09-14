"""End-to-end smoke test for the Chemistry Video Engine.

Submits 3 required chemistry questions via the HTTP API, polls until
complete (or failed/timeout), and verifies the artifact endpoint returns
a valid video/mp4 response.  Designed for 2-run repeatability checks.
"""

import asyncio
import sys
import time

import httpx

REQUIRED_CONCEPTS = [
    "How does the pH scale work?",
    "Why do atoms form covalent bonds?",
    "What is the difference between ionic and covalent bonding?",
]

BASE_URL = "http://127.0.0.1:8000/api/v1"
POLL_INTERVAL = 2
TIMEOUT_SECONDS = 120


async def test_single_query(client: httpx.AsyncClient, concept: str) -> str:
    print(f"\n[+] Submitting concept: '{concept}'")
    resp = await client.post(f"{BASE_URL}/jobs", json={"concept": concept})
    assert resp.status_code == 201, f"Create failed: {resp.text}"
    job_id = resp.json()["job_id"]
    print(f"    Job ID: {job_id}, Status: pending")

    start_time = time.time()
    while time.time() - start_time < TIMEOUT_SECONDS:
        await asyncio.sleep(POLL_INTERVAL)
        status_resp = await client.get(f"{BASE_URL}/jobs/{job_id}")
        data = status_resp.json()
        status = data["status"]
        elapsed = int(time.time() - start_time)
        print(f"    Polling job {job_id}: {status} ({elapsed}s)")
        if status == "complete":
            art_resp = await client.get(f"{BASE_URL}/jobs/{job_id}/artifact")
            assert art_resp.status_code == 200, f"Artifact fetch failed: {art_resp.status_code}"
            content_type = art_resp.headers.get("content-type", "")
            assert "video/mp4" in content_type, f"Unexpected content-type: {content_type}"
            print(f"    [SUCCESS] Video generated: {data.get('artifact_url')}")
            return job_id
        elif status == "failed":
            raise RuntimeError(
                f"Job {job_id} failed with reason: {data.get('error_reason')}"
            )

    raise TimeoutError(f"Job {job_id} timed out after {TIMEOUT_SECONDS}s")


async def run_smoke_test() -> None:
    print("=== STARTING SMOKE TEST SUITE ===")
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS + 10) as client:
        for concept in REQUIRED_CONCEPTS:
            await test_single_query(client, concept)
    print("\n=== ALL 3 REQUIRED CHEMISTRY QUERIES PASSED SUCCESSFULLY ===")


if __name__ == "__main__":
    try:
        asyncio.run(run_smoke_test())
    except (AssertionError, RuntimeError, TimeoutError) as exc:
        print(f"\n[FAIL] Smoke test failed: {exc}", file=sys.stderr)
        sys.exit(1)