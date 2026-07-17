# Evals suite port + agent-slug cleanup + akira restructure

Status: IN PROGRESS
Source discussion: 2026-07-17 session (template Q&A). Reference implementation:
`~/workspace/playground/evals/` — the proven shape this port parameterizes.

## Why

The template's eval scaffold is a stub (one metric, two graders, one pipeline,
empty reports/) while playground/evals has the mature layout: heuristic graders +
LLM judges per metric, a metrics registry, experiment runner, and HTML reports.
Evals are where this template can differentiate most for DSSG projects.

## Workstream 1 — evals port (primary)

Target layout under `_scaffold/{{ eval_root }}/` (mirrors playground/evals):

- `graders/heuristic/<metric>.py` — deterministic flags per metric
- `graders/judges/<metric>.py` + shared `judges/schema.py` (score + reasoning
  Pydantic schema), `judges/llm_judge.py` base
- `metrics/<metric>.py` — aggregates heuristic flags + judge scores
- `graders/metrics_registry.py` — single wiring point; pipelines/reports
  discover enabled metrics here, never hardcode
- `pipelines/` — `run.py` (batch grade), `sampling.py` (experiment sampling),
  `calibration.py` (heuristic-vs-judge agreement; shared, included when any
  judge is on), `redaction.py` (PII scrub step — NET NEW, not in playground;
  default-on when `data_sensitivity` in restricted/secret)
- `reports/` — builder + renderer + per-metric HTML/CSS section templates
  (port `reports/html/suite.html` + `stats.html`, make sections composable
  from the registry)

Copier axes:

- New Phase-3 multiselect `eval_metrics`: retrieval (always on — the MCP
  retrieval tool ships regardless), escalation, friction, intent, language.
- Per-metric `_tasks` removal from staging, same pattern as `integrations/`
  modules (rm the heuristic + judge + metric + report-section files for
  unselected metrics; registry renders only enabled entries via jinja).
- Genesis skill (`/project-genesis`) offers the metric list during intake.

CI: extend `.github/workflows/test-render.yml` matrix with at least one
render exercising a non-default metric set.

## Workstream 2 — agent slug cleanup

Agent directory names are hardcoded framework names (`agents/lg_agent/` etc.).
Add `agent_slug` copier var (genesis proposes it from project domain, e.g.
`intake_triage` not `lg_agent`); stage `agents/{{ agent_slug }}/` with the
framework choice picking the implementation inside. Touches: staging paths,
`_tasks` mv/rm expressions, Makefile targets (`lg-up` → `agent-up`?),
docker-compose service name, Dockerfile path, cd.yml image name, CI matrix.
Keep `rag_agent` name for the shared retrieval backend (it IS its function),
but demote it from mandatory to a default-on choice (custom-RAG option).

## Workstream 3 — akira restructure

Keep akira as an optional feature, but vendored-skill-only: drop
`src/agents/akira/` (LangGraph agent in product source) and ship just
`.claude/skills/akira` + an agent definition, matching how `akira-scan` was
globalized to ~/.claude on 2026-07-17. Rendered repos keep akira because DSSG
volunteers don't have the global config. Remove `make akira-kaneda` or repoint
it at the skill flow.

## Sequencing

1 is independent. 2 before 3 (both touch `agents/` staging + `_tasks`; akira
removal is simpler once slugs are parameterized). Each workstream = one PR.

## Done when

- Render matrix passes with metrics selected/deselected in combinations.
- A rendered project can run `pipelines/run.py` on sample data and get an HTML
  report with one section per enabled metric.
- No framework-named agent dirs in a fresh render; akira present only under
  `.claude/`.
