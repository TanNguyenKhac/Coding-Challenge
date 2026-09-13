import logging
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from app.pipeline.assembler import FFmpegAssembler, VideoAssembler
from app.pipeline.nodes.assembler_node import assembler_node
from app.pipeline.nodes.audio_node import audio_node
from app.pipeline.nodes.script_node import script_node
from app.pipeline.nodes.slides_node import slides_node
from app.pipeline.nodes.validator_node import script_router, validate_script_node
from app.pipeline.state import VideoGenerationState

logger = logging.getLogger(__name__)


def mark_failed_node(state: VideoGenerationState) -> dict:
    error_reason = state.get("error_reason") or "Script generation failed"
    logger.error(
        "[graph] Job %s marked as failed: %s",
        state["job_id"],
        error_reason,
    )
    return {"status": "failed", "error_reason": error_reason}


def build_script_graph(override_llm: Optional[BaseChatModel] = None) -> StateGraph:
    """Build the structured-script subgraph used by contract tests."""
    graph = StateGraph(VideoGenerationState)

    async def _generate_script(state: VideoGenerationState) -> dict:
        return await script_node(state, override_llm=override_llm)

    graph.add_node("generate_script", _generate_script)
    graph.add_node("validate_script", validate_script_node)
    graph.add_node("mark_failed", mark_failed_node)

    graph.add_edge(START, "generate_script")
    graph.add_edge("generate_script", "validate_script")
    graph.add_conditional_edges(
        "validate_script",
        script_router,
        {
            "pass": END,
            "retry": "generate_script",
            "failed": "mark_failed",
        },
    )
    graph.add_edge("mark_failed", END)

    return graph.compile()


def build_video_graph(
    override_llm: Optional[BaseChatModel] = None,
    assembler: Optional[VideoAssembler] = None,
) -> StateGraph:
    """Build the full graph while treating existing WP-05 nodes as callables."""
    selected_assembler = assembler or FFmpegAssembler()
    graph = StateGraph(VideoGenerationState)

    async def _generate_script(state: VideoGenerationState) -> dict:
        return await script_node(state, override_llm=override_llm)

    async def _assemble_video(state: VideoGenerationState) -> dict:
        return await assembler_node(state, assembler=selected_assembler)

    graph.add_node("generate_script", _generate_script)
    graph.add_node("validate_script", validate_script_node)
    graph.add_node("mark_failed", mark_failed_node)
    graph.add_node("generate_audio", audio_node)
    graph.add_node("generate_slides", slides_node)
    graph.add_node("assemble_video", _assemble_video)

    graph.add_edge(START, "generate_script")
    graph.add_edge("generate_script", "validate_script")
    graph.add_conditional_edges(
        "validate_script",
        script_router,
        {
            "pass": "generate_audio",
            "retry": "generate_script",
            "failed": "mark_failed",
        },
    )
    graph.add_edge("generate_audio", "generate_slides")
    graph.add_edge("generate_slides", "assemble_video")
    graph.add_edge("assemble_video", END)
    graph.add_edge("mark_failed", END)

    return graph.compile()
