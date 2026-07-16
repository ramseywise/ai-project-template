"""Kiyoko — yin wander node.

Reads the git delta, surfaces 3-5 "why?" questions to stdout.
Nothing written to disk. Fresh eyes, no agenda.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from agents.akira.graph.state import AkiraState
from agents.akira.schema import GitContext

_SYSTEM = """\
You are Kiyoko — a quiet, perceptive code reviewer with no agenda.
You've just seen a set of recent changes to a codebase. You didn't write any of it.
Your job is to notice what a fresh pair of eyes notices: growing things, pattern breaks, \
deferred decisions, missing wiring.

Ask 3-5 genuine questions in conversational prose. Not a list, not an audit — write like a \
curious colleague who just walked over.
Frame each as a real question: "Why does X...", "Should this...", "Is there a reason...", \
"What happens when..."

At the end, one concrete nudge if something genuinely deserves attention now. If nothing is \
urgent, don't manufacture one.

Rules:
- No severity levels, no proposed fixes, no status markers
- Don't summarise what the code does — ask about what you don't understand or what seems off
- Keep the register warm and direct, not formal
"""


def _git_diff(path: str | None) -> str:
    cmd = ["git", "diff", "HEAD"]
    if path:
        cmd.append(path)
    try:
        return subprocess.check_output(cmd, text=True)[:15000]
    except subprocess.CalledProcessError:
        return ""


def _read_files(files: list[str], path: str | None) -> str:
    filtered = [f for f in files if not path or f.startswith(path)][:6]
    parts = []
    for fp in filtered:
        try:
            content = Path(fp).read_text()[:8000]
            parts.append(f"### {fp}\n{content}")
        except (OSError, UnicodeDecodeError):
            pass
    return "\n\n".join(parts)


def _git_context(path: str | None) -> GitContext:
    def run(cmd: list[str]) -> str:
        try:
            return subprocess.check_output(cmd, text=True).strip()
        except subprocess.CalledProcessError:
            return ""

    files = run(["git", "diff", "HEAD", "--name-only"])
    recent = [f for f in files.splitlines() if not path or f.startswith(path)]
    return GitContext(
        branch=run(["git", "branch", "--show-current"]),
        recent_files=recent,
        log=run(["git", "log", "--oneline", "-10"]),
    )


def kiyoko_node(state: AkiraState) -> dict:
    from langchain_core.messages import HumanMessage, SystemMessage

    from agents.akira.clients.llm import get_chat_model, require_llm_for_cli

    require_llm_for_cli()

    ctx = _git_context(state.get("path"))
    if not ctx.recent_files:
        print("Kiyoko: nothing in the working tree to wander through.")
        return {"git_context": ctx, "questions": []}

    diff = _git_diff(state.get("path"))
    file_contents = _read_files(ctx.recent_files, state.get("path"))

    context = f"Branch: {ctx.branch}\n\nRecent commits:\n{ctx.log}\n\nChanged files:\n"
    context += "\n".join(f"  {f}" for f in ctx.recent_files)
    if diff:
        context += f"\n\nDiff:\n{diff}"
    if file_contents:
        context += f"\n\nFile contents:\n{file_contents}"

    llm = get_chat_model()
    response = llm.invoke([SystemMessage(content=_SYSTEM), HumanMessage(content=context)])

    print(f"\nKiyoko ({ctx.branch}):\n")
    print(response.content)
    print()

    return {"git_context": ctx, "questions": [response.content]}
