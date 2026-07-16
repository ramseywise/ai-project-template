from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from pathlib import Path

from agents.akira.schema import AkiraFinding, GitContext

log = logging.getLogger(__name__)

_JSON_BLOCK = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)

_RETURN_FORMAT = """
Return ONLY a JSON array of findings (no prose, no markdown outside the array):
[
  {
    "severity": "HIGH|MEDIUM|LOW",
    "file": "path/to/file.py",
    "line": 42,
    "title": "short title",
    "question": "Why does X...",
    "evidence": "file:line — what you found",
    "proposed_fix": "concrete action"
  }
]
If you find nothing, return an empty array: []
"""


_SKIP_DIRS = frozenset(
    {".venv", "venv", "__pycache__", ".git", "node_modules", ".mypy_cache", ".pytest_cache"}
)


def _read(path: str, limit: int = 12000) -> str:
    try:
        return Path(path).read_text()[:limit]
    except (OSError, UnicodeDecodeError):
        return f"[could not read {path}]"


def _read_dir(
    directory: str, ext: str = ".py", limit_per_file: int = 5000, max_files: int = 20
) -> str:
    parts = []
    for fp in sorted(Path(directory).rglob(f"*{ext}")):
        if any(part in _SKIP_DIRS for part in fp.parts):
            continue
        if len(parts) >= max_files:
            break
        try:
            content = fp.read_text()[:limit_per_file]
            parts.append(f"### {fp}\n{content}")
        except (OSError, UnicodeDecodeError):
            pass
    return "\n\n".join(parts)


def _parse_findings(raw: str, subagent_name: str) -> list[AkiraFinding]:
    match = _JSON_BLOCK.search(raw)
    text = match.group(1) if match else raw.strip()
    try:
        items = json.loads(text)
    except json.JSONDecodeError:
        log.warning("%s: could not parse JSON response", subagent_name)
        return []
    findings = []
    for item in items:
        try:
            findings.append(AkiraFinding(id="", subagent=subagent_name, **item))
        except Exception as e:
            log.warning("%s: skipping malformed finding: %s", subagent_name, e)
    return findings


class AkiraSubagent(ABC):
    name: str

    @abstractmethod
    async def scan(self, ctx: GitContext, path: str | None) -> list[AkiraFinding]:
        """Run domain scan and return findings."""

    async def _call(self, system: str, context: str) -> list[AkiraFinding]:
        from langchain_core.messages import HumanMessage, SystemMessage

        from agents.akira.clients.llm import get_chat_model

        llm = get_chat_model()
        prompt = system + "\n\n" + _RETURN_FORMAT
        response = await llm.ainvoke([SystemMessage(content=prompt), HumanMessage(content=context)])
        return _parse_findings(response.content, self.name)
