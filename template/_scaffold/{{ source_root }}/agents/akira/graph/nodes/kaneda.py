"""Kaneda — yang scan node.

Dispatches 5 domain subagents in parallel, aggregates findings,
writes findings/findings-{date}.md + .json.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
from datetime import date
from pathlib import Path

from agents.akira.graph.state import AkiraState
from agents.akira.schema import AkiraFinding, GitContext

_FINDINGS_DIR = Path(__file__).parents[2] / "findings"

_SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


async def _dispatch(ctx: GitContext, path: str | None) -> list[AkiraFinding]:
    from agents.akira.subagents.code_quality import CodeQualityAgent
    from agents.akira.subagents.docs_check import DocsAgent
    from agents.akira.subagents.eval_patterns import EvalAgent
    from agents.akira.subagents.safeguard import SafeguardAgent
    from agents.akira.subagents.schema_check import SchemaAgent

    agents = [
        SafeguardAgent(),
        SchemaAgent(),
        EvalAgent(),
        CodeQualityAgent(),
        DocsAgent(),
    ]
    results = await asyncio.gather(*[a.scan(ctx, path) for a in agents])
    raw = [f for batch in results for f in batch]
    raw.sort(key=lambda f: (_SEVERITY_ORDER.get(f.severity, 9), f.subagent))

    seen: set[str] = set()
    deduped: list[AkiraFinding] = []
    for f in raw:
        key = f"{f.file}:{f.title}"
        if key not in seen:
            seen.add(key)
            deduped.append(f.model_copy(update={"id": f"AK-{len(deduped) + 1:03d}"}))
    return deduped


def _write_findings(findings: list[AkiraFinding], ctx: GitContext) -> Path:
    _FINDINGS_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().strftime("%Y%m%d")
    md_path = _FINDINGS_DIR / f"findings-{today}.md"
    json_path = _FINDINGS_DIR / f"findings-{today}.json"

    counts = {s: sum(1 for f in findings if f.severity == s) for s in ("HIGH", "MEDIUM", "LOW")}
    lines = [
        f"# Akira Findings — {date.today().isoformat()}",
        f"\nScanned: {ctx.branch} | 5 subagents\n",
        f"## Summary\n{counts['HIGH']} High · {counts['MEDIUM']} Medium · {counts['LOW']} Low\n",
        "---\n",
    ]
    for f in findings:
        loc = f"{f.file}{':' + str(f.line) if f.line else ''}"
        lines += [
            f"### {f.id} [{f.severity}] {f.title}",
            f"`{f.subagent}` · `{loc}`",
            f"**Why**: {f.question}",
            f"**Evidence**: {f.evidence}",
            f"**Fix**: {f.proposed_fix}",
            "**Status**: [ ] pending\n",
            "---\n",
        ]
    md_path.write_text("\n".join(lines))
    json_path.write_text(json.dumps([f.model_dump() for f in findings], indent=2))
    return md_path


def kaneda_node(state: AkiraState) -> dict:
    def run(cmd: list[str]) -> str:
        return subprocess.check_output(cmd, text=True).strip()

    ctx = GitContext(
        branch=run(["git", "branch", "--show-current"]),
        recent_files=run(["git", "diff", "HEAD~3", "--name-only"]).splitlines(),
        log=run(["git", "log", "--oneline", "-15"]),
    )

    findings = asyncio.run(_dispatch(ctx, state.get("path")))
    md_path = _write_findings(findings, ctx)

    counts = {s: sum(1 for f in findings if f.severity == s) for s in ("HIGH", "MEDIUM", "LOW")}
    print(
        f"\nKaneda scan complete — {counts['HIGH']} High · "
        f"{counts['MEDIUM']} Medium · {counts['LOW']} Low"
    )
    print(f"Findings: {md_path}")
    print("Run make akira-dao to triage.\n")

    return {"git_context": ctx, "findings": findings}
