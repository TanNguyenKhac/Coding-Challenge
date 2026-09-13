# CHG-001 Chemistry Video MVP — Implementation Plan

## Outcome

A working FastAPI backend that accepts chemistry concept queries, generates
educational MP4 videos asynchronously, and exposes job status and artifact
retrieval through a clean REST API. Three pre-generated sample videos committed.

## Context

- Change ID: CHG-001
- Discovery handoff: artifacts/handoffs/CHG-001-discovery.yaml
- Base revision: 2cf89b0e20c3d8bfd2e7ed884770fb24b4643c72
- Timebox: 120 minutes
- Mode: architectural

## Approved option

OPT-A: Claude Haiku (script) + gTTS/pyttsx3 (audio) + Pillow (slides) + FFmpeg (MP4 assembly)

## Work packages

---

### WP-01 — Project scaffold and models

**Order:** 1  
**Owner:** backend-dev  
**Objective:** Repository has Python package structure, dependencies declared, and Pydantic models defined.

**Candidate paths:**
- app/__init__.py
- app/models.py
- requirements.txt
- .env.example

**Interfaces produced:**
- `JobStatus` enum: pending | generating | complete | failed
- `JobCreate` request model: `concept: str`
- `JobResponse` model: `job_id, concept, status, created_at, updated_at, artifact_url, error_reason`

**Test cases:** N/A (models are validated by type-checker and used in WP-02 tests)

**Commands:**
```
python -c "from app.models import JobCreate, JobResponse, JobStatus; print('ok')"
```

**Evidence expected:** Import succeeds with no errors.

**Stop conditions:**
- Dependency installation fails and cannot be resolved — report blocker.

**Dependencies:** none

---

### WP-02 — JobStore and API endpoints

**Order:** 2  
**Owner:** backend-dev  
**Objective:** Four REST endpoints are live; JobStore manages in-memory state and artifact path resolution.

**Candidate paths:**
- app/store.py
- app/routers/jobs.py
- app/main.py

**Interfaces consumed:** models from WP-01  
**Interfaces produced:**
- POST /jobs → 201 {job_id, status: "pending"}
- GET /jobs → 200 [{...}]
- GET /jobs/{id} → 200 {...} | 404
- GET /jobs/{id}/artifact → 302 redirect to /artifacts/{id}.mp4 | 404 if not complete

**Test cases (tests/test_jobs.py):**
1. POST /jobs returns 201 with job_id and status pending
2. GET /jobs returns list containing submitted job
3. GET /jobs/{id} returns job detail
4. GET /jobs/unknown-id returns 404
5. GET /jobs/{id}/artifact when not complete returns 400 or 404
6. GET /jobs/{id}/artifact when complete returns redirect to artifact file

**Commands:**
```
pytest tests/test_jobs.py -v
```

**Evidence expected:** All 6 test cases pass.

**Stop conditions:**
- If endpoint contract must change from what WP-01 models define — stop and report deviation.

**Dependencies:** WP-01

---

### WP-03 — Pipeline: ScriptProvider + validator + retry

**Order:** 3  
**Owner:** ai-dev  
**Objective:** ScriptProvider ABC, ClaudeScriptProvider (real), MockScriptProvider (test), and validator with retry logic are implemented and tested.

**Candidate paths:**
- app/pipeline/__init__.py
- app/pipeline/script_provider.py
- app/pipeline/validator.py

**Interfaces produced:**
- `ScriptProvider.generate(concept: str) -> dict` — async, raises `ScriptGenerationError` on failure
- `validate_script(script: dict) -> tuple[bool, str]` — returns (valid, reason)
- Script schema: `{title: str, sections: [{heading, narration, visual_notes}], summary: str}`
- `ClaudeScriptProvider` uses `claude-haiku-4-5-20251001`, `response_format=json_object`, system prompt enforcing schema

**Test cases (tests/test_pipeline.py):**
1. MockScriptProvider returns valid script dict
2. validate_script passes a well-formed script
3. validate_script rejects script with < 3 sections
4. validate_script rejects script with empty narration
5. validate_script rejects script with missing title
6. Orchestrator retries on first validation failure, succeeds on second (MockProvider with configurable fail_count)
7. Orchestrator sets job failed after MAX_RETRIES=2 consecutive failures

**Commands:**
```
pytest tests/test_pipeline.py -v
```

**Evidence expected:** All 7 test cases pass without requiring ANTHROPIC_API_KEY.

**Stop conditions:**
- If Haiku API returns non-JSON that cannot be fixed by prompt engineering — fall back to a structured prompt + manual JSON parse with regex guard, or escalate.

**Dependencies:** WP-01

---

### WP-04 — Pipeline: VideoProvider (Pillow + gTTS + FFmpeg)

**Order:** 4  
**Owner:** ai-dev  
**Objective:** VideoProvider ABC, FFmpegVideoProvider (real), MockVideoProvider (test stub) implemented.

**Candidate paths:**
- app/pipeline/video_provider.py

**Interfaces consumed:** validated script dict from WP-03  
**Interfaces produced:**
- `VideoProvider.generate_video(job_id: str, script: dict) -> Path` — async, returns path to MP4
- `FFmpegVideoProvider`: renders Pillow slides (1280×720), generates per-section gTTS audio (fallback pyttsx3), assembles with FFmpeg
- `MockVideoProvider`: writes a minimal valid 1-frame MP4 stub to artifacts/{job_id}.mp4 using FFmpeg or a pre-baked binary stub

**Slide layout:**
- Background: dark blue (#1a1a2e)
- Title card: white heading, subtitle text
- Section card: heading (yellow), narration text (white), visual_notes (grey italic)
- Font: system monospace or bundled fallback

**Test cases:**
- `MockVideoProvider.generate_video(...)` creates a file at the expected path
- File is non-empty

**Commands:**
```
pytest tests/test_pipeline.py::test_mock_video_provider -v
```

**Evidence expected:** Mock video file created; test passes without FFmpeg.

**Stop conditions:**
- FFmpeg binary not found — MockVideoProvider must still work; real provider skips gracefully with a documented error.

**Dependencies:** WP-03

---

### WP-05 — Orchestrator wiring and end-to-end smoke test

**Order:** 5  
**Owner:** backend-dev  
**Objective:** `run_job` orchestrator connects script generation, validation/retry, and video generation; job state transitions are correct; smoke test script passes.

**Candidate paths:**
- app/pipeline/orchestrator.py
- scripts/smoke_test.py

**Orchestrator contract:**
```
async def run_job(job_id: str, concept: str, store: JobStore,
                  script_provider: ScriptProvider,
                  video_provider: VideoProvider,
                  max_retries: int = 2) -> None
```
State transitions:
- pending → generating (immediately on entry)
- generating → complete (after video saved)
- generating → failed (after max_retries exceeded or video provider error)

**Test cases:**
1. run_job with MockScriptProvider + MockVideoProvider transitions to complete
2. run_job with always-failing MockScriptProvider transitions to failed after retries
3. Smoke test: real providers with ANTHROPIC_API_KEY — all three required concepts reach complete

**Commands:**
```
pytest tests/test_pipeline.py::test_orchestrator -v
ANTHROPIC_API_KEY=... python scripts/smoke_test.py
```

**Evidence expected:**
- Unit tests pass without API key
- Smoke test produces three MP4 files in artifacts/

**Stop conditions:**
- If API key is unavailable — unit tests still pass; smoke test is deferred to WP-06.

**Dependencies:** WP-02, WP-04

---

### WP-06 — Pre-generate three sample videos and commit

**Order:** 6  
**Owner:** ai-dev  
**Objective:** Three MP4 artifacts for the required chemistry queries are generated and committed to artifacts/samples/.

**Candidate paths:**
- artifacts/samples/job-ph-scale.mp4
- artifacts/samples/job-covalent-bonds.mp4
- artifacts/samples/job-ionic-vs-covalent.mp4
- artifacts/samples/README.md (lists query → file mapping)

**Commands:**
```
ANTHROPIC_API_KEY=... python scripts/generate_samples.py
ffprobe artifacts/samples/*.mp4
```

**Evidence expected:** Three non-zero MP4 files, each parseable by ffprobe, committed to the repo.

**Stop conditions:**
- If generation fails validation after MAX_RETRIES on two consecutive runs — report as pipeline defect before committing.

**Dependencies:** WP-05

---

### WP-07 — README.md and ARCHITECTURE.md

**Order:** 7  
**Owner:** backend-dev  
**Objective:** README and architecture documents satisfy AC-011 and AC-012.

**Candidate paths:**
- README.md
- ARCHITECTURE.md

**README sections required:**
1. Prerequisites (Python 3.11+, FFmpeg, ANTHROPIC_API_KEY)
2. Installation (`pip install -r requirements.txt`)
3. Run (`uvicorn app.main:app --reload`)
4. API reference (curl examples for all four endpoints)
5. Testing (`pytest`)
6. Sample videos (pointer to artifacts/samples/)

**ARCHITECTURE sections required:**
1. Job lifecycle diagram (text/ASCII)
2. Persistence and artifact boundary (JobStore as sole writer)
3. AI/video generation boundary (provider interface, swap instructions)
4. Cost table (model, tokens/call, cost/1K tokens, total cost/video)
5. What was optimized for

**Commands:**
```
# Manual review — no automated check
```

**Evidence expected:** Both files present and cover all required topics.

**Dependencies:** WP-06

---

## Verification contract

See `artifacts/handoffs/CHG-001-discovery.yaml` §verification_contract for full details.

Required checks in order:
1. `pytest tests/ -v` — all unit tests pass without API key
2. `python scripts/smoke_test.py` — three concepts complete end-to-end (requires API key + FFmpeg)
3. `ffprobe artifacts/samples/*.mp4` — all three sample artifacts are valid MP4

Repeatability: run smoke_test.py twice; both runs must complete without manual intervention.

## Risks and mitigations

See `artifacts/handoffs/CHG-001-discovery.yaml` §risks for full list.

Key: RSK-004 (timebox) — if WP-04 real video assembly is not complete within time, MockVideoProvider stubs satisfy unit tests; WP-06 can commit pre-generated stubs.

## Progress

| WP    | Status  | Notes |
|-------|---------|-------|
| WP-01 | pending |       |
| WP-02 | pending |       |
| WP-03 | pending |       |
| WP-04 | pending |       |
| WP-05 | pending |       |
| WP-06 | pending |       |
| WP-07 | pending |       |
