"""Chat model factory for the akira subagents — they use LangChain message types
(SystemMessage/HumanMessage) directly, unlike this project's other agents which
call the Anthropic SDK straight (see agents/lg_agent/clients/llm.py's comment on
why: no tool-calling loop needed there). Akira's subagents are LLM-driven judges
composing prompts generically, which is exactly langchain-anthropic's use case."""

from __future__ import annotations

from functools import lru_cache

from langchain_anthropic import ChatAnthropic

from agents.akira.settings import settings


@lru_cache(maxsize=1)
def get_chat_model() -> ChatAnthropic:
    return ChatAnthropic(model=settings.akira_model, anthropic_api_key=settings.anthropic_api_key)


def require_llm_for_cli() -> None:
    if not settings.anthropic_api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set — akira's kiyoko/dao modes need a real LLM call. "
            "Set it in .env before running `make akira-kiyoko` or `make akira-dao`."
        )
