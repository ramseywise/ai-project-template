# AI-Eng Claude Template

A [Copier](https://copier.readthedocs.io/en/stable/) template that drops the Claude Code AI-engineering tooling from my agentic `playground` repo — a research→plan→execute→review skill pipeline, hook-based code-quality enforcement, and an optional parameterized MCP server — into a new or already-existing project.

## What you get

Three tiers — not one flat bundle. The interview no longer walks the tiers question-by-question:
it runs in **phases** (see "The interview" below), and the tiers describe what lands on disk:

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

This prompts through the phased interview (see below) and renders the result into `output_dir`. Use
`make new_project_dev` instead while iterating on the template itself, so it renders from your dirty
working tree rather than requiring a commit first.

## The interview

Questions are ordered around **discovery, not implementation** — you say what you're building first,
and the implementation choices either derive their defaults from that or aren't asked at all:

1. **Phase 1 — Project scoping** (always asked): name/slug/description, `project_type` (chat app /
   autonomous agent / workflow automation / RAG / MCP server / AI backend / eval suite / research
   prototype / layer-onto-existing-repo), `primary_users`, `primary_backend_language`,
   `external_systems` (multiselect: Slack, GitHub, Google Workspace, Calendar, Email, Database, Web),
   `deployment_target`.
2. **Phase 1b — The AI system itself** (agent-shaped projects only): `agent_tools` (multiselect),
   `agent_memory` (none / conversation / long-term), `human_approval` (none / sometimes / always).
   These land in the generated `DESIGN.md`'s Key Decisions table and seed architecture defaults
   (MCP on when tools include MCP; postgres checkpointer on for long-term memory).
3. **Phase 2 — Architecture** (each asked only when Phase 1 makes it relevant): `primary_chat_agent`
   (skipped for MCP-server/eval-suite projects), `vector_backend` (asked only for RAG projects or when
   Database is an external system — defaults to `postgres` in the latter case), `ts_agent_framework`
   (TS projects; defaults to `vercel_ai_sdk` for TS-only chat/agent projects), `frontend_backend_topology`
   (only when there's both a TS component and a Python backend), `include_mcp_server` +
   `mcp_server_language` (language follows `primary_backend_language`).
4. **Phase 3 — Optional features**: one `optional_features` multiselect (akira, dev companion,
   promptfoo, ragas, web research, meeting intelligence, marketing clients, n8n webhook, composio,
   ml labs) instead of ten yes/no prompts. Defaults are seeded from Phase 1 — e.g. Web → web research,
   Slack/GitHub/Email → composio, workflow project → n8n webhook. Calendar isn't in the list: selecting
   Calendar as an external system already scaffolds the Google Calendar client.
5. **Phase 4 — Team conventions**: `data_sensitivity` (default follows `primary_users` —
   customer/public-facing → `restricted`), `ticket_prefix`, `enable_macos_notifications`.

Everything else is **inferred, never asked**: `source_root` (`src`), `eval_root`/`eval_allowed_dirs`,
`enable_structure_guard` (on only for eval-suite/RAG shapes), `python_version` (3.12), `aws_region`,
`ts_source_root`/`ts_project_root`, `mcp_server_name`/`mcp_server_slug`, `scaffold_full_project`
(false only for the layer-onto-existing-repo project type), `has_typescript`, and each `include_*`
feature toggle (derived from the multiselect). Every inferred value remains overridable
non-interactively — `-d source_root=lib`, `-d scaffold_full_project=false`, `-d include_ml_labs=true`
all still work, which is how CI and `/project-genesis` drive the template.

## Updating a project that already used this template

Copier tracks the answers it was given in `.copier-answers.yml`. Re-run `copier update` from inside the
generated project to pull in template changes — see the
[Copier update docs](https://copier.readthedocs.io/en/stable/updating/).

## Options

**Asked** (grouped by interview phase):

| Question | Default | Notes |
|---|---|---|
| `project_type` | `chat_app` | What you're building — drives which later questions appear and every derived default. `existing_repo` = layering-only mode |
| `primary_users` | `internal` | `internal`/`customers`/`developers`/`public_api` — seeds `data_sensitivity` and DESIGN.md's actor table |
| `primary_backend_language` | `python` | `python`/`typescript`/`both` — `typescript`/`both` scaffold a real Node/TS backend service at `ts_project_root` (package.json, tsconfig, eslint, Jest), not just frontend hooks |
| `external_systems` | *(none)* | Multiselect: Slack/GitHub/Google Workspace/Calendar/Email/Database/Web — seeds integration + vector-store defaults |
| `deployment_target` | `local` | `local`/`docker`/`cloud`/`serverless` — recorded in DESIGN.md's Key Decisions |
| `agent_tools` | `[mcp]` + seeded | Agent-shaped projects only. Multiselect; `mcp` seeds `include_mcp_server`; recorded in DESIGN.md |
| `agent_memory` | `conversation` | Agent-shaped projects only. `long_term` seeds `enable_postgres_checkpointer=true`; recorded in DESIGN.md |
| `human_approval` | `sometimes` | Agent-shaped projects only. Recorded in DESIGN.md — constrains tools that write to external systems |
| `primary_chat_agent` | derived from `project_type` | `lg_agent`/`adk_agent`/`both`/`none` — which chat agent(s) join the always-present `rag_agent`. Skipped for `mcp_server`/`eval_suite` projects |
| `vector_backend` | `duckdb` (`postgres` if Database selected) | Asked only for RAG projects or when Database is an external system. `opensearch` adds `opensearch-py`; `postgres` (pgvector — works with Supabase) adds `psycopg`/`pgvector` |
| `ts_agent_framework` | `vercel_ai_sdk` for TS-only chat/agent projects, else `none` | Asked only for agent-shaped TS projects — stages a real streamText + tool() loop at `<ts_project_root>/src/agent/` |
| `frontend_backend_topology` | `single` | Asked only with both a TS component and a Python backend. `split_service` = Next.js (Vercel) + FastAPI (Railway) sharing Supabase-JWT identity |
| `include_mcp_server` | `true` when project is an MCP server or agent tools include MCP | Scaffolds `mcp_servers/<slug>/` |
| `mcp_server_language` | follows `primary_backend_language` | `python` (FastMCP) or `typescript` (official MCP TS SDK) — independent of the backend language, the default just follows it |
| `optional_features` | `[akira, dev_companion]` + seeded | One multiselect replacing ten `include_*` prompts — see "Optional features" below |
| `data_sensitivity` | `internal` (`restricted` for customer/public-facing) | `public`/`internal`/`restricted`/`secret` — drives a `CLAUDE.md` hard rule and (when `scaffold_full_project`) a Terraform resource tag |
| `ticket_prefix` | `LIN` | Drives branch-naming enforcement and the Linear-ticket skill |
| `enable_macos_notifications` | `true` | Turn off on Linux/CI |

**Optional features** (values of the `optional_features` multiselect; each maps to a derived
`include_*` variable that `-d` can still override individually):

| Value | Derived variable | What it scaffolds |
|---|---|---|
| `akira` (default on) | `include_akira` | A second prebuilt LangGraph agent for proactive codebase quality scanning (kiyoko/kaneda/dao modes) |
| `dev_companion` (default on) | `include_dev_companion` | A living "how we work on this project" doc (transforms, not appends) plus a `/dream` maintenance-audit skill |
| `promptfoo` (seeded by `eval_suite`) | `include_promptfoo` | `promptfoo.config.yaml` — config-driven eval harness (`npx promptfoo eval`) hitting `rag_agent`'s `/chat` endpoint, alongside the Python eval suite |
| `ragas` | `include_ragas_grader` | ragas-based LLM-judge grader. **Known issue** (verified 2026-07-14): `ragas` 0.4.3 has a broken import upstream — degrades gracefully, no real scores until fixed |
| `web_research` (seeded by Web) | `include_web_research` | `integrations/web_research.py` — autonomous web research + reports via GPT-Researcher (needs Python ≤ 3.13) |
| `meeting_intelligence` | `include_meeting_intelligence` | `integrations/meeting_intelligence.py` — transcript → structured action items/decisions via one LLM call |
| `marketing` | `include_marketing_integrations` | `integrations/{eventbrite,linkedin,canva}.py` — thin clients for publishing events, posting updates, generating assets |
| `n8n_webhook` (seeded by `workflow`) | `include_n8n_webhook` | HMAC-verified inbound webhook receiver (`POST /webhooks/n8n`), auto-mounted on every present agent's FastAPI app |
| `composio` (seeded by Slack/GitHub/Email/Workspace) | `include_composio` | `integrations/composio.py` — third-party app actions via Composio's unified tool API |
| `ml_labs` | `include_ml_labs` | `labs/` — classical ML/stats toolkit (regression, time-series, A/B testing, feature engineering, model comparison, clustering) |

`include_calendar_integration` (`integrations/google_calendar.py`, pre-obtained OAuth2 refresh token)
isn't in the multiselect — it derives directly from Calendar in `external_systems`.

**Inferred, never asked** (all overridable with `-d name=value`):

| Variable | Default | Notes |
|---|---|---|
| `scaffold_full_project` | `true` unless `project_type=existing_repo` | The old top-level toggle — `false` = layering-only mode |
| `has_typescript` | from `primary_backend_language` | Adds TS quality + typecheck hooks; `-d has_typescript=true` for a frontend-only layering project |
| `source_root` / `ts_source_root` / `ts_project_root` | `src` / `src` / `<project_slug>` | Directory layout |
| `eval_root` / `eval_allowed_dirs` | `evals` / `graders metrics pipelines reports utils` | Eval-suite layout |
| `enable_structure_guard` | on only for `eval_suite`/`rag` shapes | Canonical eval-suite directory enforcement |
| `enable_postgres_checkpointer` | `vector_backend=postgres` or `agent_memory=long_term` | Adds `langgraph-checkpoint-postgres`; runtime default stays `memory` either way |
| `python_version` / `aws_region` | `3.12` / `eu-central-1` | pyproject floor / Terraform default region |
| `mcp_server_name` / `mcp_server_slug` | `<project_slug>` | MCP server naming |
| `expensive_command_patterns` | *(blank)* | Regex for commands that should nudge `--dry-run`; blank disables the hook |
| `include_agent_reference_library` | `true` | `.agents/skills/` (ADK + LangGraph reference library) + `/new-agent` |
| `global_skills_source` | `vendored` | Maintainer knob — see `scripts/sync-global-skills.sh` |

## Design notes

- Everything here was extracted from `playground/.claude/`, stripped of client- and domain-specific
  content (no client names, no music-KB domain logic, no VA-project package paths).
- Unlike `ds-python-project-template`, there's no `git init`/initial-commit task — this template is meant
  to be layered onto a project that may already exist and already have its own git history.
- All Python-stack assumptions (`uv`, `pytest`, `ruff`, `pyright`) are load-bearing defaults, not yet
  optional — this template currently targets Python (+ optional TypeScript) projects.
