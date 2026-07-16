from __future__ import annotations

from typing_extensions import TypedDict

from agents.akira.schema import AkiraFinding, AkiraMode, GitContext


class AkiraState(TypedDict):
    mode: AkiraMode
    path: str | None  # optional scope filter
    git_context: GitContext | None
    questions: list[str]  # kiyoko output
    findings: list[AkiraFinding]  # kaneda output
    error: str | None
