# AI-Eng Claude Template

A [Copier](https://copier.readthedocs.io/en/stable/) template that drops the Claude Code AI-engineering tooling from my agentic `playground` repo — a research→plan→execute→review skill pipeline, hook-based code-quality enforcement, and an optional parameterized MCP server — into a new or already-existing project.

## What you get

Three tiers — not one flat bundle. `copier.yaml`'s questions span all three, interleaved; this is the
grouping that actually matters:

1. **Always scaffolded**: `CLAUDE.md` (style conventions, hook-enforced standards, commit convention, a
   placeholder for project-specific hard rules — plus a data-classification hard rule driven by
   `data_sensitivity`), `.claude/settings.json` (hook wiring: secrets scan, branch naming, code quality,
   test coverage, SDK-pattern checks, docs hygiene, memory-duplication guard, commit gates), and
   `.claude/hooks/*.sh` + `.claude/skills/` (21 workflow skills — research-review, plan-review,
   execute-plan, code-review, quick-pr, mcp-builder, new-agent, etc. — see `.claude/skills/README.md` in
   the generated project for the full map).
2. **Independent toggles** (available even with `scaffold_full_project=false`, i.e. layering-only mode
   onto an existing repo): `.agents/skills/` (`include_agent_reference_library`) — a tool-agnostic
   ADK/LangGraph reference library that `/new-agent` orchestrates — and `mcp_servers/<slug>/`
   (`include_mcp_server`) — a FastMCP server scaffold, ready to extend.
3. **One all-or-nothing bundle** behind `scaffold_full_project`: `pyproject.toml`, `core/` ingestion,
   `evals/`, `infrastructure/`, `tests/`, CI, `.pre-commit-config.yaml` (ruff-pre-commit, reads the same
   `[tool.ruff]` config as everything else — real git-level enforcement alongside the Claude-session
   hooks) and `renovate.json` (automated dependency-update PRs, with the fast-moving AI framework deps
   held back from automerge) — plus the sub-gated `include_akira`/`include_dev_companion` toggles within
   this tier. Working example agents: `rag_agent` (embedding-based retrieval, the shared backend the MCP
   tool calls) always ships within this tier; `primary_chat_agent` picks which user-facing chat agent(s)
   join it — `lg_agent` (LangGraph, BM25), `adk_agent` (Google ADK), `both` (default, today's behavior),
   or `none` (build your own on top of `rag_agent` alone). `langgraph`/`langchain-core` stay installed
   regardless of this choice — `rag_agent` and `akira` both depend on them; only the chosen chat agent's
   own framework-specific deps (`langchain-mcp-adapters` for `lg_agent`, `google-adk`+`mcp` for
   `adk_agent`) actually toggle. The eval suite grades every backend independently (see `evals/README.md`
   in the generated project), so this choice never breaks eval coverage.

This repo's own `.github/workflows/test-render.yml` renders a representative config matrix (defaults,
layering-only, each `primary_chat_agent` value) on every push/PR and checks for leftover Jinja + a clean
`ruff check`/`format --check` — the automated version of this session's manual verification loop.

## Quick start

**Recommended sequence (two skills):**

1. `/scope-poc` — system design interview. Asks about actors, problem, MVP scope, and key architectural
   decisions before touching infrastructure. Produces `DESIGN.md`. DSSG-aware: recognizes
   `nonprofit-success-ai` and `project-mgmt-ai` and applies shared platform context automatically.

2. `/project-genesis` — infrastructure interview. Reads `DESIGN.md` if it exists (many questions
   are already answered), asks about agent framework, vector backend, TypeScript, MCP, then runs
   copier non-interactively.

Running `/project-genesis` alone (skipping `/scope-poc`) is valid — the generated project includes a
blank `DESIGN.md` stub as a reminder to fill in the design before sprint 1.

**Power-user/scriptable path** — the same copier prompts directly:

```bash
make new_project output_dir="~/Workspace/my-project" project_name="My Project"
```

This prompts through the remaining options (source directory name, ticket prefix, data sensitivity,
whether to include TypeScript hooks, the eval-suite structure guard, and the MCP server scaffold) and
renders the result into `output_dir`. Use `make new_project_dev` instead while iterating on the template
itself, so it renders from your dirty working tree rather than requiring a commit first.

## Updating a project that already used this template

Copier tracks the answers it was given in `.copier-answers.yml`. Re-run `copier update` from inside the
generated project to pull in template changes — see the
[Copier update docs](https://copier.readthedocs.io/en/stable/updating/).

## Options

| Question | Default | Notes |
|---|---|---|
| `data_sensitivity` | `internal` | `public`/`internal`/`restricted`/`secret` — drives a `CLAUDE.md` hard rule and (when `scaffold_full_project`) a Terraform resource tag |
| `source_root` | `src` | Hooks that scope checks to source files use this |
| `ticket_prefix` | `LIN` | Drives branch-naming enforcement and the Linear-ticket skill |
| `enable_structure_guard` | `false` | Turn on only for eval-suite-shaped repos (e.g. RAG/agent evals) |
| `primary_backend_language` | `python` (when `scaffold_full_project`) | `python`/`typescript`/`both` — `typescript`/`both` scaffold a real Node/TS backend service at `ts_project_root` (package.json, tsconfig, eslint, Jest), not just frontend hooks |
| `has_typescript` | auto (`true` if `primary_backend_language` includes `typescript`, else `false`) | Adds TS quality + typecheck hooks; can be set independently for a frontend-only, layering-only TS project |
| `mcp_server_language` | `python` (when `include_mcp_server`) | `python` (FastMCP) or `typescript` (official MCP TS SDK) — independent of `primary_backend_language` |
| `enable_macos_notifications` | `true` | Turn off on Linux/CI |
| `expensive_command_patterns` | *(blank)* | Regex for commands that should nudge `--dry-run`; blank disables the hook |
| `include_agent_reference_library` | `true` | Scaffolds `.agents/skills/` (ADK + LangGraph reference library) and enables `/new-agent` |
| `include_akira` | `true` (when `scaffold_full_project`) | Scaffolds `akira`, a second prebuilt LangGraph agent for proactive codebase quality scanning (kiyoko/kaneda/dao modes) |
| `include_dev_companion` | `true` (when `scaffold_full_project`) | Adds a living "how we work on this project" doc (transforms, not appends) plus a `/dream` maintenance-audit skill |
| `include_mcp_server` | `true` | Scaffolds `mcp_servers/<slug>/` with a FastMCP (or TS, see `mcp_server_language`) placeholder tool |
| `primary_chat_agent` | `both` (when `scaffold_full_project`) | `lg_agent`/`adk_agent`/`both`/`none` — which chat agent(s) join the always-present `rag_agent` |
| `vector_backend` | `duckdb` (when `scaffold_full_project`) | `duckdb`/`memory`/`opensearch`/`postgres` — rag_agent's vector store; `opensearch` adds the optional `opensearch-py` dependency, `postgres` (pgvector — works with Supabase) adds `psycopg`/`pgvector` |
| `enable_postgres_checkpointer` | `true` if `vector_backend=postgres` else `false` | Adds `langgraph-checkpoint-postgres` so `lg_agent`/`rag_agent`'s LangGraph checkpointer can be set to `postgres` (`POSTGRES_DSN`) at runtime — independent of `vector_backend` |
| `include_n8n_webhook` | `false` (when `scaffold_full_project`) | Scaffolds a generic HMAC-verified inbound webhook receiver (`POST /webhooks/n8n`), auto-mounted on every present agent's FastAPI app |
| `include_calendar_integration` | `false` (when `scaffold_full_project`) | Scaffolds `integrations/google_calendar.py` (list/create events, find availability) using a pre-obtained OAuth2 refresh token |
| `include_marketing_integrations` | `false` (when `scaffold_full_project`) | Scaffolds `integrations/{eventbrite,linkedin,canva}.py` — thin clients for publishing events, posting updates, generating assets |
| `include_meeting_intelligence` | `false` (when `scaffold_full_project`) | Scaffolds `integrations/meeting_intelligence.py` — extracts structured action items/decisions from a meeting transcript via one LLM call |
| `include_ragas_grader` | `false` (when `scaffold_full_project`) | Adds a ragas-based LLM-judge grader to the eval suite. **Known issue** (verified 2026-07-14): current `ragas` (0.4.3) has a broken import upstream — this module degrades gracefully rather than crashing, but produces no real scores until ragas ships a fix |
| `include_promptfoo` | `false` (when `scaffold_full_project`) | Adds `promptfoo.config.yaml` — a config-driven eval harness (`npx promptfoo eval`) hitting `rag_agent`'s `/chat` endpoint directly, alongside the Python eval suite |
| `include_composio` | `false` (when `scaffold_full_project`) | Scaffolds `integrations/composio.py` — discover/execute third-party app actions (Gmail, Slack, GitHub, ...) via Composio's unified tool API |
| `include_web_research` | `false` (when `scaffold_full_project`) | Scaffolds `integrations/web_research.py` — autonomous web research + report generation via GPT-Researcher |
| `include_ml_labs` | `false` (when `scaffold_full_project`) | Scaffolds `labs/` — a classical ML/stats toolkit (regression, time-series, A/B testing, feature engineering, model comparison, clustering) orthogonal to the agentic-AI focus |

## Design notes

- Everything here was extracted from `playground/.claude/`, stripped of client- and domain-specific
  content (no client names, no music-KB domain logic, no VA-project package paths).
- Unlike `ds-python-project-template`, there's no `git init`/initial-commit task — this template is meant
  to be layered onto a project that may already exist and already have its own git history.
- All Python-stack assumptions (`uv`, `pytest`, `ruff`, `pyright`) are load-bearing defaults, not yet
  optional — this template currently targets Python (+ optional TypeScript) projects.
