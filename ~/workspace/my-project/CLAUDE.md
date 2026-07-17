# My Project

TODO: describe this project

## Layout

```
my-project/
├── src/              Application source
├── tests/                          Unit, smoke, and integration tests
├── mcp_servers/my-project/   MCP server — see mcp_servers/my-project/app/server.py
├── .agents/skills/                 Tool-agnostic ADK/LangGraph reference library — see .agents/skills/README.md
├── .claude/skills/akira/  Proactive quality scans (vendored skill + akira-scan agent) — see its SKILL.md
├── .claude/docs/companion/          Living "how we work" doc — see .claude/skills/grow-companion/SKILL.md
```

## Refs (read before writing code here)

<!-- Machine-wide stack conventions; skip any that don't exist on this machine. -->
- `~/.claude/refs/python.md`, `~/.claude/refs/logging.md`

Folder-level refs live in nested CLAUDE.md stubs (auto-load on file access):

## Hard Rules

<!-- Add project-specific hard rules here, e.g. confidentiality/naming boundaries, module ownership,
     directory allowlists. These are enforced by hooks in .claude/hooks/ where automatable —
     document the ones that can't be — see .claude/hooks/ for the current hook-enforced set. -->

1. Tests live at root `tests/`, not inside `src/`.
2. `.claude/docs/plans/` and `.claude/docs/reviews/` are scratch/local workspace — never commit them. Promote durable findings into project docs instead.
4. Data classification: **internal**.

## Style

- `from __future__ import annotations` in all modules
- Type annotations on all signatures; f-strings only
- `httpx` not `requests`; async-first I/O
- Pydantic models at API boundaries
- No magic numbers — named constants or env vars

## Hook-Enforced Standards

**PostToolUse (Write|Edit):** ruff format + check, no `print()` in src/, no bare `except`, no mutable default arguments, no hardcoded model strings, no bare LLM/tracing-client instantiation outside factory files, secrets scan, file size warning >400 lines.

**PreToolUse (Bash):** `git commit` blocked if tests fail or `uv.lock` is out of sync, `.claude/docs/plans/` or `.claude/docs/reviews/` blocked from being staged or committed, `pip install` blocked (use `uv add`), destructive commands blocked.

See `.claude/skills/README.md` for the full skill inventory.

## Commit Convention

```
<type>: <description>
```

Types: `feat`, `fix`, `chore`, `refactor`, `docs`, `test`, `perf`, `ci`
