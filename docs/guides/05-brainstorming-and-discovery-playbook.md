# 05. Playbook: From Brainstorming & Ideation to Production Code

## 1. The Pitfalls of Naive AI Brainstorming

When developers prompt AI with high-level ideas (e.g., *"Make the video generator support 3D animations for chemical bonds"*), unguided AI systems typically:
1. Immediately dump hundreds of lines of speculative code into existing files.
2. Make unvalidated assumptions about database models, schemas, and dependencies.
3. Break existing working functionality without realization.

This playbook provides a structured, repeatable methodology to transform a **vague idea** into **solid architecture**, **bounded work packages**, and **verified production code**.

---

## 2. The 4-Step Discovery Playbook

```text
[STEP 1: BRAINSTORMING & REPOSITORY INSPECTION]
  │  Prompt: "I want to introduce feature X..."
  ▼
[STEP 2: CLASSIFICATION & CLARIFYING QUESTIONS]
  │  AI classifies Work Shape (Spike / Bounded / Architectural)
  │  AI returns `needs-input` with critical decision-changing questions
  ▼
[STEP 3: DISCOVERY HANDOFF GENERATION]
  │  Emits formal design, Work Packages, Allowed Paths & Test Oracles
  ▼
 ╔═════════════════════════════════════════════════════════════════════╗
 ║ GATE H1: Architecture & Scope Approval (Human Sign-off)            ║
 ╚═════════════════════════════════════════════════════════════════════╝
  │
  ▼
[STEP 4: EXECUTION & INDEPENDENT VERIFICATION]
  │  Implement (Devs) ──► Verify (Reviewer Read-only) ──► Gate H3 (Release)
```

---

## 3. Step-by-Step Execution

### Step 1: Initiate Discovery with `$wf-discover`
Introduce your high-level concept via `$wf-discover`. The `architect` subagent engages in read-only analysis:

```text
User: "Design an automated pipeline to split Chemistry video scripts into discrete scenes, generate isolated TTS audio files for each scene, and concatenate the final video using FFmpeg."
```

### Step 2: Information Classification & The "Clarifying Questions" Pattern (`needs-input`)
Rather than making wild assumptions, the `architect` categorizes discovered context into 5 distinct tiers:
1. **Authoritative**: Established in `docs/specs/SPEC-03-llm-structured-script.md` and `SPEC-04-media-chunk-assembly.md`.
2. **Observed**: Existing code generates full audio as a single continuous MP3 (`app/services/audio.py`).
3. **Derived**: Scene-level splitting will simplify visual animation timing synchronization.
4. **Decision Required**: Human must select the TTS provider strategy and latency tolerance.
5. **Unknown**: What is the maximum allowed duration per scene chunk?

The agent pauses and emits `needs-input` with a focused, decision-changing question:
> **Architect Clarification**: *"Should we integrate ElevenLabs API (higher fidelity, metered cost) or Edge-TTS (free, local generation) for scene audio chunks? And what is the maximum duration threshold per scene?"*

### Step 3: Human Clarification & Handoff Contract Generation
Once the engineer clarifies requirements, the `architect` outputs `artifacts/handoffs/CHG-003-discovery.yaml`:

```yaml
schema: discovery-handoff/v2
change_id: CHG-003
status: ready-for-approval
repository_mode: brownfield
base_revision: "0e901d4"
requirements:
  - id: REQ-SCENE-SPLIT
    title: "Decompose Chemistry Script into discrete Scene chunks"
  - id: REQ-TTS-CHUNK
    title: "Generate isolated Edge-TTS audio per Scene"
  - id: REQ-FFMPEG-CONCAT
    title: "Assemble video and audio chunks into final MP4 using FFmpeg"
acceptance_criteria:
  - id: AC-01
    title: "Script output contains at least 3 scenes with duration_ms and narration"
    oracle: "pytest tests/unit/test_scene_splitter.py passes"
  - id: AC-02
    title: "Generates valid MP4 with scene-synchronized audio tracks"
    oracle: "pytest tests/integration/test_media_assembly.py passes"
work_packages:
  - id: PKG-01
    title: "AI Pipeline: Update StateGraph & Scene Splitter"
    agent: ai-dev
    allowed_paths:
      - "app/pipeline/nodes/script_node.py"
      - "app/pipeline/nodes/splitter_node.py"
      - "app/schemas/script.py"
      - "tests/unit/test_scene_splitter.py"
  - id: PKG-02
    title: "Media Service: Implement FFmpeg Concat Service & Edge-TTS"
    agent: backend-dev
    allowed_paths:
      - "app/services/tts_service.py"
      - "app/services/video_composer.py"
      - "tests/integration/test_media_assembly.py"
risks:
  - id: RSK-FFMPEG-CODEC
    description: "FFmpeg concatenation fails if audio chunk sample rates differ"
    mitigation: "Standardize all audio chunks to PCM WAV 44.1kHz prior to concatenation"
```

### Step 4: Gate H1 Approval & Handover to Implementation
The engineer inspects the discovery artifact. If satisfied with the scope, work packages, and allowed paths:
1. Issue **Gate H1 Approval**: *"Approved H1 for CHG-003"*.
2. Trigger `$wf-implement`: `ai-dev` and `backend-dev` execute their respective packages in parallel without mutual interference.
3. Trigger `$wf-verify`: `reviewer` executes the test suite independently and compiles the verification report for Gate H3 sign-off.

---

## 4. Key Takeaways

With this disciplined approach:
- **Vague ideas** are systematically refined into concrete, testable specifications.
- **Unverified code** is physically prevented from entering the codebase.
- **The engineer retains complete architectural control**, while AI handles bounded implementation and rigorous validation.
