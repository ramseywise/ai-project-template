from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool

from ..clients.llm import agenerate
from ..clients.mcp import get_mcp_tools
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

    for _ in range(_MAX_TOOL_TURNS):
        response = await agenerate(system_prompt, messages, tools=anthropic_tools)
        if response.stop_reason != "tool_use":
            text = "".join(block.text for block in response.content if block.type == "text")
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
                    result_text = str(await tool.ainvoke(block.input))
                except Exception as exc:
                    result_text = f"Tool error: {exc}"
            tool_results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": result_text}
            )
        messages.append({"role": "user", "content": tool_results})

    return {"answer": "Reached max tool-call turns without a final answer."}
