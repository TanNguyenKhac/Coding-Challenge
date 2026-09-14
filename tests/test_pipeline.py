import ast
import copy
import inspect
import os
import time
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from PIL import Image
from pydantic import ValidationError

import app.llm_factory as llm_factory_module
from app.llm_factory import build_llm
from app.pipeline.assembler import FFmpegAssembler, MockAssembler
from app.pipeline.graph import build_script_graph, build_video_graph
from app.pipeline.nodes.assembler_node import assembler_node
from app.pipeline.nodes.audio_node import audio_node, generate_single_audio
from app.pipeline.nodes.script_node import script_node
from app.pipeline.nodes.slides_node import render_single_slide, slides_node
from app.pipeline.nodes.validator_node import script_router, validate_script_node
from app.pipeline.state import VideoGenerationState
from app.schemas.job import VideoConfig
from app.schemas.script import ScriptChunk, VideoScript
from tests.conftest import make_mock_structured_llm


def _make_state(
    concept: str = "pH scale",
    retry_count: int = 0,
    script=None,
    error_reason=None,
    job_id: str = "test-job-id",
) -> VideoGenerationState:
    return VideoGenerationState(
        job_id=job_id,
        concept=concept,
        config=VideoConfig(),
        retry_count=retry_count,
        status="generating",
        script=script,
        error_reason=error_reason,
        audio_paths=[],
        slide_paths=[],
        artifact_path=None,
    )


class TestGraphTopology:
    def test_state_has_approved_required_and_optional_keys(self):
        assert VideoGenerationState.__required_keys__ == {
            "job_id",
            "concept",
            "config",
            "retry_count",
            "status",
        }
        assert VideoGenerationState.__optional_keys__ == {
            "script",
            "error_reason",
            "audio_paths",
            "slide_paths",
            "artifact_path",
        }

    def test_graph_compiles(self):
        graph = build_script_graph()
        assert graph is not None

    def test_video_graph_compiles(self):
        graph = build_video_graph(assembler=MockAssembler())
        assert graph is not None

    def test_video_graph_has_approved_nodes_without_retry_adapter(self):
        graph = build_video_graph(assembler=MockAssembler()).get_graph()
        node_names = set(graph.nodes)

        assert {
            "generate_script",
            "validate_script",
            "generate_audio",
            "generate_slides",
            "assemble_video",
            "mark_failed",
        }.issubset(node_names)
        assert "retry_script" not in node_names

    @pytest.mark.asyncio
    async def test_graph_with_mock_llm_valid_script(self, valid_script):
        mock_llm = make_mock_structured_llm([valid_script])
        graph = build_script_graph(override_llm=mock_llm)

        result = await graph.ainvoke(_make_state())

        assert result["error_reason"] is None
        assert result["script"] == valid_script
        assert mock_llm.invocation_count == 1

    @pytest.mark.asyncio
    async def test_graph_retries_twice_then_accepts_valid_script(
        self,
        invalid_script_few_chunks,
        valid_script,
    ):
        mock_llm = make_mock_structured_llm(
            [invalid_script_few_chunks, invalid_script_few_chunks, valid_script]
        )
        graph = build_script_graph(override_llm=mock_llm)

        result = await graph.ainvoke(_make_state())

        assert result["script"] == valid_script
        assert result["retry_count"] == 2
        assert result["error_reason"] is None
        assert result["status"] == "generating"
        assert mock_llm.invocation_count == 3

    @pytest.mark.asyncio
    async def test_graph_fails_after_exactly_two_retries(self, invalid_script_few_chunks):
        mock_llm = make_mock_structured_llm([invalid_script_few_chunks])
        graph = build_script_graph(override_llm=mock_llm)

        result = await graph.ainvoke(_make_state())

        assert result["status"] == "failed"
        assert result["retry_count"] == 3
        assert result["error_reason"]
        assert mock_llm.invocation_count == 3


class TestScriptNode:
    def test_script_schema_accepts_valid_contract(self, valid_script):
        round_tripped = VideoScript.model_validate(valid_script.model_dump())

        assert round_tripped == valid_script
        assert round_tripped.chunks[0].duration_hint_sec is None

    def test_script_schema_rejects_malformed_and_incomplete_contracts(self, valid_script):
        valid_payload = valid_script.model_dump()

        missing_summary = copy.deepcopy(valid_payload)
        missing_summary.pop("summary")
        too_few_chunks = copy.deepcopy(valid_payload)
        too_few_chunks["chunks"] = too_few_chunks["chunks"][:2]
        short_heading = copy.deepcopy(valid_payload)
        short_heading["chunks"][0]["heading"] = "x"
        short_narration = copy.deepcopy(valid_payload)
        short_narration["chunks"][0]["narration"] = "short"
        short_visual_notes = copy.deepcopy(valid_payload)
        short_visual_notes["chunks"][0]["visual_notes"] = "x"
        missing_chunk_id = copy.deepcopy(valid_payload)
        missing_chunk_id["chunks"][0].pop("chunk_id")

        for payload in (
            missing_summary,
            too_few_chunks,
            short_heading,
            short_narration,
            short_visual_notes,
            missing_chunk_id,
        ):
            with pytest.raises(ValidationError):
                VideoScript.model_validate(payload)

    @pytest.mark.asyncio
    async def test_script_node_uses_typed_async_structured_output(self, valid_script):
        mock_llm = make_mock_structured_llm([valid_script])

        result = await script_node(_make_state(), override_llm=mock_llm)

        assert result["script"] == valid_script
        assert isinstance(result["script"], VideoScript)
        assert mock_llm.bound_schemas == [VideoScript]
        assert mock_llm.invocation_count == 1
        assert mock_llm.structured.sync_invocation_attempts == 0

    @pytest.mark.asyncio
    async def test_script_node_validates_mapping_returned_by_fake(self, valid_script):
        mock_llm = make_mock_structured_llm([valid_script.model_dump()])

        result = await script_node(_make_state(), override_llm=mock_llm)

        assert isinstance(result["script"], VideoScript)
        assert result["script"] == valid_script

    @pytest.mark.asyncio
    async def test_script_node_maps_structured_output_error(self):
        broken_llm = make_mock_structured_llm([RuntimeError("Connection error")])

        result = await script_node(_make_state(), override_llm=broken_llm)

        assert result["script"] is None
        assert result["error_reason"] == "LLM Generation Error: Connection error"

    def test_script_node_contains_no_regex_or_manual_parser(self):
        source = inspect.getsource(script_node)
        tree = ast.parse(source)

        assert "with_structured_output(VideoScript)" in source
        assert "structured_llm.ainvoke" in source
        assert all(
            not (isinstance(node, ast.Name) and node.id == "re")
            for node in ast.walk(tree)
        )


class TestValidatorNode:
    def test_validator_passes_valid_script(self, valid_script):
        state = _make_state(script=valid_script)

        result = validate_script_node(state)

        assert result == {"error_reason": None}

    def test_validator_fails_few_chunks_and_counts_attempt(self, invalid_script_few_chunks):
        state = _make_state(script=invalid_script_few_chunks)

        result = validate_script_node(state)
        routed_state = state | result

        assert "chunks" in result["error_reason"]
        assert result["retry_count"] == 1
        assert script_router(routed_state) == "retry"

    def test_validator_fails_no_script_and_preserves_provider_error(self):
        state = _make_state(script=None, error_reason="Provider unavailable")

        result = validate_script_node(state)

        assert result["error_reason"] == "Provider unavailable"
        assert result["retry_count"] == 1

    def test_validator_rejects_whitespace_heading(self, valid_script):
        invalid_chunk = ScriptChunk.model_construct(
            chunk_id=0,
            heading="  ",
            narration="This narration remains long enough for the schema.",
            visual_notes="A valid visual description",
            duration_hint_sec=None,
        )
        script = VideoScript.model_construct(
            title=valid_script.title,
            summary=valid_script.summary,
            chunks=[invalid_chunk, *valid_script.chunks[1:]],
        )

        result = validate_script_node(_make_state(script=script))

        assert "empty heading or narration" in result["error_reason"]

    def test_router_returns_pass(self, valid_script):
        state = _make_state(script=valid_script, error_reason=None)
        assert script_router(state) == "pass"

    def test_router_allows_second_retry(self, invalid_script_few_chunks):
        state = _make_state(
            script=invalid_script_few_chunks,
            error_reason="too few chunks",
            retry_count=1,
        )
        routed_state = state | validate_script_node(state)

        assert routed_state["retry_count"] == 2
        assert script_router(routed_state) == "retry"

    def test_router_fails_after_second_retry(self, invalid_script_few_chunks):
        state = _make_state(
            script=invalid_script_few_chunks,
            error_reason="too few chunks",
            retry_count=2,
        )
        routed_state = state | validate_script_node(state)

        assert routed_state["retry_count"] == 3
        assert script_router(routed_state) == "failed"


class TestLLMFactory:
    def test_build_llm_with_override(self, valid_script):
        serialized = valid_script.model_dump_json()
        mock_llm = FakeListChatModel(responses=[serialized])
        result = build_llm(override_llm=mock_llm)
        assert result is mock_llm

    def test_build_llm_maps_codex_provider_deterministically(self, monkeypatch):
        fake_settings = SimpleNamespace(
            codex_api_base="http://local-codex.invalid/v1",
            codex_api_key="",
            codex_model="",
            anthropic_api_key="unused-fallback-key",
        )
        monkeypatch.setattr(llm_factory_module, "settings", fake_settings)
        sentinel = object()

        with patch("langchain_openai.ChatOpenAI", return_value=sentinel) as constructor:
            result = llm_factory_module.build_llm()

        assert result is sentinel
        constructor.assert_called_once_with(
            base_url="http://local-codex.invalid/v1",
            api_key="not-needed",
            model="codex-mini-latest",
            temperature=0,
        )

    def test_build_llm_maps_anthropic_provider_deterministically(self, monkeypatch):
        fake_settings = SimpleNamespace(
            codex_api_base=None,
            codex_api_key="unused",
            codex_model="unused",
            anthropic_api_key="deterministic-test-key",
        )
        monkeypatch.setattr(llm_factory_module, "settings", fake_settings)
        sentinel = object()

        with patch("langchain_anthropic.ChatAnthropic", return_value=sentinel) as constructor:
            result = llm_factory_module.build_llm()

        assert result is sentinel
        constructor.assert_called_once_with(
            api_key="deterministic-test-key",
            model="claude-haiku-4-5-20251001",
            temperature=0,
        )

    def test_build_llm_no_provider_raises(self, monkeypatch):
        fake_settings = SimpleNamespace(
            codex_api_base=None,
            codex_api_key="unused",
            codex_model="unused",
            anthropic_api_key=None,
        )
        monkeypatch.setattr(llm_factory_module, "settings", fake_settings)

        with pytest.raises(RuntimeError, match="No LLM provider"):
            llm_factory_module.build_llm()


class TestVideoNodes:
    @pytest.mark.asyncio
    async def test_mock_assembler(self, tmp_path, valid_script):
        start_time = time.time()
        assembler = MockAssembler()
        out_dir = str(tmp_path / "videos")
        out_path = await assembler.assemble(
            job_id="test-mock-job",
            script=valid_script,
            audio_paths=["a1.mp3", "a2.mp3"],
            slide_paths=["s1.png", "s2.png"],
            output_dir=out_dir,
        )
        elapsed = time.time() - start_time

        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) > 0
        assert elapsed < 0.05
        with open(out_path, "rb") as file:
            header = file.read(16)
            assert b"ftypmp42" in header

    @pytest.mark.asyncio
    async def test_slides_node_parallel(self, valid_script):
        state = _make_state(script=valid_script, job_id="test-slides-job")
        result = await slides_node(state)

        slide_paths = result.get("slide_paths")
        assert slide_paths is not None
        assert len(slide_paths) == len(valid_script.chunks)

        for path in slide_paths:
            assert os.path.exists(path)
            with Image.open(path) as image:
                assert image.size == (1280, 720)

    @pytest.mark.asyncio
    async def test_audio_node_parallel_with_mock(self, valid_script):
        def fake_audio_gen(chunk, out_path, lang="vi"):
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as file:
                file.write(b"FAKE_AUDIO_BYTES")
            return out_path

        state = _make_state(script=valid_script, job_id="test-audio-job")
        with patch(
            "app.pipeline.nodes.audio_node.generate_single_audio",
            side_effect=fake_audio_gen,
        ):
            result = await audio_node(state)

        audio_paths = result.get("audio_paths")
        assert audio_paths is not None
        assert len(audio_paths) == len(valid_script.chunks)
        for path in audio_paths:
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0

    @pytest.mark.asyncio
    async def test_audio_node_fallback_to_pyttsx3(self, tmp_path):
        chunk = ScriptChunk(
            chunk_id=0,
            heading="Fallback Test",
            narration="Testing the deterministic offline text to speech fallback.",
            visual_notes="A fallback audio waveform",
        )
        out_file = str(tmp_path / "fallback.mp3")

        with patch("app.pipeline.nodes.audio_node.gTTS", side_effect=Exception("Network unreachable")):
            generated_path = generate_single_audio(chunk, out_file, lang="vi")
            assert os.path.exists(generated_path)
            assert os.path.getsize(generated_path) > 0

    @pytest.mark.asyncio
    async def test_assembler_node(self, valid_script):
        state = _make_state(script=valid_script, job_id="test-assemble-node")
        state["audio_paths"] = ["a0.mp3", "a1.mp3", "a2.mp3"]
        state["slide_paths"] = ["s0.png", "s1.png", "s2.png"]

        result = await assembler_node(state, assembler=MockAssembler())

        assert result["status"] == "complete"
        assert result["artifact_path"] is not None
        assert os.path.exists(result["artifact_path"])

    @pytest.mark.asyncio
    async def test_full_video_graph_with_mock_assembler(self, valid_script):
        mock_llm = make_mock_structured_llm([valid_script])
        graph = build_video_graph(
            override_llm=mock_llm,
            assembler=MockAssembler(),
        )
        initial_state = _make_state(job_id="full-graph-test-job")

        def fake_audio_gen(chunk, out_path, lang="vi"):
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as file:
                file.write(b"AUDIO")
            return out_path

        with patch(
            "app.pipeline.nodes.audio_node.generate_single_audio",
            side_effect=fake_audio_gen,
        ):
            final_state = await graph.ainvoke(initial_state)

        assert final_state["status"] == "complete"
        assert final_state["artifact_path"] is not None
        assert os.path.exists(final_state["artifact_path"])
        assert len(final_state["audio_paths"]) == 3
        assert len(final_state["slide_paths"]) == 3

    @pytest.mark.asyncio
    async def test_ffmpeg_assembler_real(self, tmp_path, valid_script):
        out_dir = str(tmp_path / "ffmpeg_test")
        os.makedirs(out_dir, exist_ok=True)

        slide_path = render_single_slide(
            valid_script.chunks[0],
            valid_script.title,
            os.path.join(out_dir, "slide_0.png"),
            resolution=(640, 360),
            chunk_index=0,
        )

        import subprocess

        audio_path = os.path.join(out_dir, "audio_0.mp3")
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=44100:cl=mono",
                "-t",
                "1",
                "-c:a",
                "libmp3lame",
                audio_path,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        assembler = FFmpegAssembler()
        final_mp4 = await assembler.assemble(
            job_id="test-ffmpeg-job",
            script=valid_script,
            audio_paths=[audio_path],
            slide_paths=[slide_path],
            output_dir=out_dir,
        )

        assert os.path.exists(final_mp4)
        assert os.path.getsize(final_mp4) > 1000
