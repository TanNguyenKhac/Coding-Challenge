import logging
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel

from app.config import settings

logger = logging.getLogger(__name__)


def build_llm(override_llm: Optional[BaseChatModel] = None) -> BaseChatModel:
    if override_llm is not None:
        return override_llm

    if settings.codex_api_base:
        from langchain_openai import ChatOpenAI

        logger.info(f"Using Codex LLM at {settings.codex_api_base}")
        return ChatOpenAI(
            base_url=settings.codex_api_base,
            api_key=settings.codex_api_key or "not-needed",
            model=settings.codex_model or "codex-mini-latest",
            temperature=0,
        )

    if settings.anthropic_api_key:
        from langchain_anthropic import ChatAnthropic

        logger.info("Using Anthropic Claude Haiku LLM")
        return ChatAnthropic(
            api_key=settings.anthropic_api_key,
            model="claude-haiku-4-5-20251001",
            temperature=0,
        )

    raise RuntimeError(
        "No LLM provider configured. Set CODEX_API_BASE or ANTHROPIC_API_KEY in environment."
    )
