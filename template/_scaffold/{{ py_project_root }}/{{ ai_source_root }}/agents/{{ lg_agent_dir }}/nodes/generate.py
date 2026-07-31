from __future__ import annotations

import asyncio
from typing import Any

from langchain_core.tools import BaseTool

from context_budget.context_budget import compact_history, should_compact, track_usage
from observability.spans import chat_span, execute_tool_span

from ..clients.llm import agenerate, get_client
from ..clients.mcp import get_mcp_tools
from ..settings import settings
from ..stall_detector import StallDetectedError, StallDetector
from ..state import State

_SYSTEM_PROMPT = """You are a support assistant answering questions using the provided \
context articles and any tools available to you. If neither the context nor a tool \
call can answer the question, say so plainly instead of guessing. Be concise.

Context:
{context}
"""

# Safety valve against a tool-call loop that never converges — not a quality target.
_MAX_TOOL_TURNS = 4


def _to_anthropic_tool(tool: BaseTool) -> dict:
    # langchain-mcp-adapters sets args_schema to the tool's raw JSON schema dict
    # (MCP tools are JSON-schema-native) rather than a pydantic model — pass it
    # through directly instead of calling a pydantic method that isn't there.
    if isinstance(tool.args_schema, dict):
        schema = tool.args_schema
    else:
        schema = {"type": "object", "properties": tool.args}
    return {"name": tool.name, "description": tool.description or "", "input_schema": schema}


async def generate_node(state: State) -> dict:
    if state.get("blocked", False):
        return {"answer": state.get("block_reason", "")}

    context_snippets = state.get("context_snippets", [])
    context = "\n\n---\n\n".join(context_snippets) or "(no matching articles found)"
    system_prompt = _SYSTEM_PROMPT.format(context=context)

    mcp_tools = await get_mcp_tools()
    tools_by_name = {tool.name: tool for tool in mcp_tools}
    anthropic_tools = [_to_anthropic_tool(tool) for tool in mcp_tools]

    messages: list[dict[str, Any]] = [{"role": "user", "content": state["message"]}]
    stall = StallDetector()

    for _ in range(_MAX_TOOL_TURNS):
        with chat_span(model=settings.lg_model):
            response = await agenerate(system_prompt, messages, tools=anthropic_tools)

        track_usage(response)
        if should_compact(response):
            # compact_history calls client.messages.create synchronously; run in a
            # thread pool so the blocking call does not stall the async event loop.
            messages = await asyncio.to_thread(
                compact_history, messages, get_client(), model=settings.lg_model
            )

        if response.stop_reason != "tool_use":
            text = "".join(block.text for block in response.content if block.type == "text")
            try:
                stall.record_output(text)
            except StallDetectedError as exc:
                return {"answer": f"Stall detected in LLM output: {exc}"}
            return {"answer": text}

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            tool = tools_by_name.get(block.name)
            if tool is None:
                result_text = f"Unknown tool: {block.name}"
            else:
                try:
                    stall.record_tool_call(block.name, block.input)
                    with execute_tool_span(tool_name=block.name, inputs=block.input):
                        result_text = str(await tool.ainvoke(block.input))
                except StallDetectedError as exc:
                    return {"answer": f"Stall detected in tool loop: {exc}"}
                except Exception as exc:
                    result_text = f"Tool error: {exc}"
            tool_results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": result_text}
            )
        messages.append({"role": "user", "content": tool_results})

    return {"answer": "Reached max tool-call turns without a final answer."}
