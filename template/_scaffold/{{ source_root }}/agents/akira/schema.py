from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class AkiraMode(StrEnum):
    kiyoko = "kiyoko"  # yin: wander, perceive, ask
    kaneda = "kaneda"  # yang: scan, dispatch, structure
    dao = "dao"  # the path — triage, apply, test


class AkiraFinding(BaseModel):
    id: str = Field(description="Sequential ID: AK-001, AK-002, ...")
    severity: Literal["HIGH", "MEDIUM", "LOW"]
    subagent: str
    file: str
    line: int | None = None
    title: str
    question: str = Field(description="Why-framed question raised by the subagent")
    evidence: str = Field(description="file:line references supporting the finding")
    proposed_fix: str
    status: Literal["pending", "done", "reverted", "superseded"] = "pending"


class GitContext(BaseModel):
    branch: str
    recent_files: list[str]
    log: str
