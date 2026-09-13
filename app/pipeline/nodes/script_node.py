import logging
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.llm_factory import build_llm
from app.pipeline.state import VideoGenerationState
from app.schemas.script import VideoScript

logger = logging.getLogger(__name__)

CHEMISTRY_SYSTEM_PROMPT_REVISION = "spec-03-v1"
CHEMISTRY_SYSTEM_PROMPT = """You are an expert chemistry educator creating structured, high-impact video scripts for students.
Your explanation must be clear, accurate, engaging, and visually descriptive.
Always return structured data matching the VideoScript schema with at least 3 distinct pedagogical chunks:
1. Introduction & Hook: Real-world chemistry context and core question.
2. Molecular / Concept Mechanism: How molecules, electrons, bonds, or reactions work at the molecular level.
3. Summary & Takeaway: Key principle and practical application.
"""


async def script_node(
    state: VideoGenerationState,
    override_llm: Optional[BaseChatModel] = None,
) -> dict:
    """Generate and validate a typed script without manual text parsing."""
    concept = state["concept"]
    config = state["config"]
    retry_count = state.get("retry_count", 0)

    logger.info(
        "[script_node] Generating script for concept=%r, attempt=%s",
        concept,
        retry_count + 1,
    )

    try:
        llm = build_llm(override_llm)
        structured_llm = llm.with_structured_output(VideoScript)
        messages = [
            SystemMessage(content=CHEMISTRY_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Explain the following chemistry concept:\n{concept}\n\n"
                    "Parameters:\n"
                    f"- Target duration: ~{config.target_duration_sec} seconds\n"
                    f"- Target audience: {config.target_audience}\n"
                    f"- Language: {config.language}\n"
                    "Break down the explanation into at least 3 cohesive, clear visual scenes."
                )
            ),
        ]

        structured_output = await structured_llm.ainvoke(messages)
        script = (
            structured_output
            if isinstance(structured_output, VideoScript)
            else VideoScript.model_validate(structured_output)
        )
        return {"script": script, "retry_count": retry_count}
    except Exception as exc:
        logger.warning("[script_node] Structured output error: %s", exc)
        return {
            "script": None,
            "error_reason": f"LLM Generation Error: {exc}",
            "retry_count": retry_count,
        }


# Preserve the existing repository entry point while exposing the SPEC-03 name.
generate_script_node = script_node
