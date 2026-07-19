from __future__ import annotations

from functools import lru_cache

import anthropic

from integrations.settings import settings


@lru_cache(maxsize=1)
def get_client() -> anthropic.Anthropic:
    """The only place in integrations/ allowed to instantiate the Anthropic
    client directly — see .claude/hooks/sdk_lint.sh's sdk-factory check."""
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)
