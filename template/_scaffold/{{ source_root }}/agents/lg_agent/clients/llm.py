from __future__ import annotations

from functools import lru_cache

import anthropic

from agents.lg_agent.settings import settings


@lru_cache(maxsize=1)
def get_client() -> anthropic.Anthropic:
    """The only place allowed to instantiate the Anthropic client directly —
    see .claude/hooks/sdk_lint.sh's sdk-factory check."""
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


@lru_cache(maxsize=1)
def get_async_client() -> anthropic.AsyncAnthropic:
    """The only place allowed to instantiate the async Anthropic client —
    see .claude/hooks/sdk_lint.sh's sdk-factory check."""
    return anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)


def generate(system_prompt: str, user_message: str) -> str:
    client = get_client()
    response = client.messages.create(
        model=settings.lg_model,
        max_tokens=1024,
        temperature=settings.generation_temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    usage = response.usage
    print(f"[lg_agent] tokens in={usage.input_tokens} out={usage.output_tokens}")
    for block in response.content:
        if block.type == "text":
            return block.text
    return ""


async def agenerate(
    system_prompt: str,
    messages: list[dict],
    tools: list[dict] | None = None,
) -> anthropic.types.Message:
    """One turn of an async, tool-capable generation.

    Returns the raw Message so the caller can inspect `.stop_reason` and handle
    `tool_use` blocks — loop policy (max turns, what counts as "done") is
    agent-specific and belongs in the node, not this factory.
    """
    client = get_async_client()
    response = await client.messages.create(
        model=settings.lg_model,
        max_tokens=1024,
        temperature=settings.generation_temperature,
        system=system_prompt,
        messages=messages,
        tools=tools or [],
    )
    usage = response.usage
    print(f"[lg_agent] tokens in={usage.input_tokens} out={usage.output_tokens}")
    return response
