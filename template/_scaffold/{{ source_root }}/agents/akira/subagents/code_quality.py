"""CodeQualityAgent.

Question: What's too long, too coupled, or missing tests — especially in recently-touched code?
"""

from __future__ import annotations

from agents.akira.schema import AkiraFinding, GitContext

from .base import AkiraSubagent, _read

_SYSTEM = """\
You are CodeQualityAgent, reviewing recently-touched code for quality issues.

Look for:
- Functions or methods over 80 lines — flag with "what's the one thing this does?"
- Non-trivial public functions with no corresponding test in tests/unit
- Hardcoded timeouts, model names, or thresholds not going through settings.py / env vars
- Unused imports or dead helpers that are defined but never called
- Comments that explain WHAT instead of WHY (they rot and mislead)
"""


class CodeQualityAgent(AkiraSubagent):
    name = "CodeQualityAgent"

    async def scan(self, ctx: GitContext, path: str | None) -> list[AkiraFinding]:
        files = [f for f in ctx.recent_files if f.endswith(".py")]
        if path:
            files = [f for f in files if f.startswith(path)]
        files = files[:6]

        context = f"Recently touched files on branch {ctx.branch}:\n"
        for fp in files:
            content = _read(fp)
            line_count = len(content.splitlines())
            context += f"\n\n## {fp} ({line_count} lines)\n{content}"

        if not files:
            context += "\nNo recently touched Python files found."

        return await self._call(_SYSTEM, context)
