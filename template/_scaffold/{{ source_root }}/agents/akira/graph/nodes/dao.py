"""Dao — the path node.

Reads the most recent findings doc, applies all pending findings,
runs make test after each. Reverts on failure. Writes run summary.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import date
from pathlib import Path

from agents.akira.graph.state import AkiraState
from agents.akira.schema import AkiraFinding

_FINDINGS_DIR = Path(__file__).parents[2] / "findings"


def _load_findings(path: str | None) -> tuple[Path, list[AkiraFinding]]:
    docs = sorted(_FINDINGS_DIR.glob("findings-*.md"), reverse=True)
    if not docs:
        raise FileNotFoundError("No findings doc found. Run make akira-kaneda first.")

    md_path = docs[0]
    json_path = md_path.with_suffix(".json")
    if not json_path.exists():
        raise FileNotFoundError(f"No JSON alongside {md_path.name} — findings may be malformed.")

    all_findings = [AkiraFinding(**f) for f in json.loads(json_path.read_text())]

    # Markdown is source of truth for status — skip anything already actioned
    processed: set[str] = set()
    current_id: str | None = None
    for line in md_path.read_text().splitlines():
        if line.startswith("### AK-"):
            current_id = line.split()[1]
        if current_id and "**Status**:" in line and "[ ] pending" not in line:
            processed.add(current_id)
            current_id = None

    to_apply = [f for f in all_findings if f.id not in processed]
    if path:
        to_apply = [f for f in to_apply if f.file.startswith(path)]
    return md_path, to_apply


def _run_tests() -> bool:
    result = subprocess.run(["make", "test"], capture_output=True, text=True)
    return result.returncode == 0


_TRIAGE_VERDICTS = ("disregard", "auto_fix", "needs_review")


def _assess_finding(finding: AkiraFinding) -> tuple[str, str]:
    """Three-way triage before touching anything.

    Returns (verdict, reason) where verdict is one of:
    - disregard:    false positive, already fixed, truncation artifact, intentional design
    - auto_fix:     real issue, single-file targeted change, low blast radius
    - needs_review: real issue but requires new file, multi-file change, or architectural decision
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    from agents.akira.clients.llm import get_chat_model

    fp = Path(finding.file)
    if fp.exists():
        content = fp.read_text()[:12000]
    else:
        content = "[file not found — may be a new-file finding]"

    system = """\
Triage a codebase finding before attempting a fix. Classify into exactly one:

disregard    — false positive, truncation artifact, already fixed, "unconfirmed" (subagent \
flagged uncertainty not a confirmed bug), or intentional design difference
auto_fix     — confirmed real issue, single-file targeted change with clear before/after \
(rename, type fix, add import, fix constant, update docs table row). Low blast radius.
needs_review — real issue but requires: new file creation, multi-file change, behavioral change, \
test authoring, or architectural decision — surface to user, do not auto-apply

Reply format:
Line 1: exactly one word — disregard, auto_fix, or needs_review
Line 2: one sentence explaining the classification"""

    context = (
        f"[{finding.severity}] {finding.subagent}: {finding.title}\n"
        f"Evidence: {finding.evidence}\n"
        f"Proposed fix: {finding.proposed_fix}\n\n"
        f"File ({finding.file}):\n{content}"
    )

    llm = get_chat_model()
    response = llm.invoke([SystemMessage(content=system), HumanMessage(content=context)])
    lines = response.content.strip().splitlines()
    verdict = lines[0].strip().lower()
    reason = lines[1].strip() if len(lines) > 1 else ""

    if verdict not in _TRIAGE_VERDICTS:
        verdict = "needs_review"

    return verdict, reason


def _apply_fix(finding: AkiraFinding) -> bool:
    from langchain_core.messages import HumanMessage, SystemMessage

    from agents.akira.clients.llm import get_chat_model

    fp = Path(finding.file)
    if not fp.exists():
        return False

    original = fp.read_text()

    system = """\
You are applying a single targeted fix to a Python file.
Return ONLY the complete updated file content — no prose, no markdown fences, no explanation.
Preserve all existing formatting, imports, and comments unrelated to the fix.
Make the minimal change needed to address the finding.
"""
    context = f"""Finding: {finding.title}
Question: {finding.question}
Proposed fix: {finding.proposed_fix}
Evidence: {finding.evidence}

Current file ({finding.file}):
{original}"""

    llm = get_chat_model()
    response = llm.invoke([SystemMessage(content=system), HumanMessage(content=context)])
    updated = response.content.strip()

    if updated.startswith("```"):
        lines = updated.splitlines()
        updated = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    fp.write_text(updated)
    return True


def _revert(file: str) -> None:
    subprocess.run(["git", "checkout", "--", file], check=False)


def _update_status(md_path: Path, finding_id: str, status: str) -> None:
    text = md_path.read_text()
    lines = text.splitlines()
    in_finding = False
    for i, line in enumerate(lines):
        if line.startswith(f"### {finding_id} "):
            in_finding = True
        if in_finding and "**Status**:" in line:
            lines[i] = f"**Status**: [{status}]"
            break
    md_path.write_text("\n".join(lines))


def _write_run_summary(
    md_path: Path,
    applied: list[tuple[AkiraFinding, str]],
    needs_review: list[tuple[AkiraFinding, str]],
    dismissed: list[tuple[AkiraFinding, str]],
) -> None:
    """Replace the ## Summary block with a narrative, themed attribution report."""
    from collections import Counter

    text = md_path.read_text()

    counts_match = re.search(r"(\d+) High · (\d+) Medium · (\d+) Low", text)
    h = int(counts_match.group(1)) if counts_match else 0
    m = int(counts_match.group(2)) if counts_match else 0
    lo = int(counts_match.group(3)) if counts_match else 0
    total = h + m + lo

    all_findings = [f for f, _ in applied + needs_review + dismissed]
    subagent_counts = Counter(f.subagent for f in all_findings)
    theme_parts = [f"{cnt} {agent}" for agent, cnt in subagent_counts.most_common()]
    theme_str = " · ".join(theme_parts) if theme_parts else "none"

    lines = [
        "## Summary",
        "",
        f"**Scan:** {total} findings — {h} High · {m} Medium · {lo} Low",
        f"**Themes:** {theme_str}",
        f"**Result:** {len(applied)} applied · {len(needs_review)} open for review"
        f" · {len(dismissed)} dismissed — {date.today().isoformat()}",
    ]

    if applied:
        lines += ["", "### Applied"]
        for f, _ in applied:
            lines.append(f"- **{f.id}** `{f.file}` — {f.title}")

    if needs_review:
        lines += ["", "### Open for review"]
        for f, reason in needs_review:
            lines.append(f"- **{f.id}** [{f.severity}] `{f.file}` — {f.title}")
            lines.append(f"  *{reason}*")

    if dismissed:
        lines += ["", "### Dismissed"]
        for f, reason in dismissed:
            lines.append(f"- **{f.id}** {f.title} — *{reason}*")

    lines.append("")
    new_block = "\n".join(lines)
    updated = re.sub(r"## Summary.*?(?=\n---)", new_block, text, count=1, flags=re.DOTALL)
    md_path.write_text(updated)


def dao_node(state: AkiraState) -> dict:
    try:
        md_path, to_apply = _load_findings(state.get("path"))
    except FileNotFoundError as e:
        print(f"Dao: {e}")
        return {"error": str(e)}

    if not to_apply:
        print("Dao: no pending findings — run make akira-kaneda to scan.")
        return {}

    if not _run_tests():
        print("Dao: tests fail before any changes — fix pre-existing failures first.")
        return {"error": "pre-existing test failures"}

    from agents.akira.clients.llm import require_llm_for_cli

    require_llm_for_cli()

    applied: list[tuple[AkiraFinding, str]] = []
    needs_review: list[tuple[AkiraFinding, str]] = []
    dismissed: list[tuple[AkiraFinding, str]] = []

    for finding in to_apply:
        print(f"  -> {finding.id} [{finding.severity}] {finding.title}")
        verdict, reason = _assess_finding(finding)
        print(f"    {verdict}: {reason}")

        if verdict == "disregard":
            _update_status(md_path, finding.id, "superseded")
            dismissed.append((finding, reason))

        elif verdict == "needs_review":
            needs_review.append((finding, reason))

        else:  # auto_fix
            if not _apply_fix(finding):
                continue
            if _run_tests():
                _update_status(md_path, finding.id, "done")
                print("    applied")
                applied.append((finding, reason))
            else:
                _revert(finding.file)
                _update_status(md_path, finding.id, "reverted")
                print("    reverted — tests failed")
                needs_review.append(
                    (
                        finding,
                        "auto-fix failed: tests broke after applying change — apply manually",
                    )
                )

    _write_run_summary(md_path, applied, needs_review, dismissed)

    print(
        f"\nDao: applied {len(applied)} · open for review {len(needs_review)} · "
        f"dismissed {len(dismissed)}"
    )
    if needs_review:
        print(f"  -> {len(needs_review)} items need human attention — see {md_path.name}")
    if len(applied) > 3:
        print("  -> run /code-review before PR")

    return {}
