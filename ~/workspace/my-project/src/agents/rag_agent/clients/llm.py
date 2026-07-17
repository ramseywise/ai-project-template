from __future__ import annotations

from functools import lru_cache

import anthropic

from agents.rag_agent.settings import settings


@lru_cache(maxsize=1)
def get_client() -> anthropic.Anthropic:
    """The only place allowed to instantiate the Anthropic client directly —
    see .claude/hooks/sdk_lint.sh's sdk-factory check."""
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def generate(system_prompt: str, user_message: str) -> str:
    client = get_client()
    response = client.messages.create(
        model=settings.rag_model,
        max_tokens=1024,
        temperature=settings.generation_temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    usage = response.usage
    print(f"[rag_agent] tokens in={usage.input_tokens} out={usage.output_tokens}")
    for block in response.content:
        if block.type == "text":
            return block.text
    return ""
