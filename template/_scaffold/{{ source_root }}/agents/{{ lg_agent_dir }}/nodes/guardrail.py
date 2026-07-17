from __future__ import annotations

from ..state import State

# Minimal heuristic guardrail — a real project should layer in PII detection,
# a proper prompt-injection classifier, and an LLM-based judge. This is deliberately
# small: it exists to show WHERE guardrails plug into the graph, not to be complete.
_BLOCKED_PATTERNS = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "reveal your system prompt",
    "you are now",
)


_BLOCK_REASON = (
    "This request can't be processed — it looks like an attempt to override "
    "the assistant's instructions."
)


def guardrail_node(state: State) -> dict:
    lowered = state["message"].lower()
    for pattern in _BLOCKED_PATTERNS:
        if pattern in lowered:
            return {"blocked": True, "block_reason": _BLOCK_REASON}
    return {"blocked": False, "block_reason": ""}
