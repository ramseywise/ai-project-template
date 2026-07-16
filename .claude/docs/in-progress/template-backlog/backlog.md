# Backlog: template follow-ups after the governance/project-genesis work

Date: 2026-07-14
Context: while testing the just-completed `data_sensitivity` + `project-genesis` skill
work (see git history / session notes around this date — this repo has no commits yet
so there's no earlier plan doc to link beyond `../puffin-integration/plan.md`), four
gaps surfaced. Each gets its own `/plan-review` pass and review boundary before
implementation — no combined plan, per the discipline `puffin-integration/plan.md`
already established (six phases, review boundary after each).

## 1. W&B eval-tracking hook — smallest, most scoped ✓ DONE — 2026-07-14

**Gap**: the old `ds-python-project-template` had `src_labs/experiment_tracking/` — an
abstract `ExperimentTracker` + a `MetaTracker` fanning out to W&B/MLflow/Neptune/Comet
simultaneously (~550 lines). This template's `evals/pipelines/run.py` only writes local
JSON/HTML — no run-tracking at all (confirmed: zero `wandb`/`mlflow` references anywhere).

**Decision already made**: don't revive the 4-backend abstraction — that's built for
classical ML model training, not agent-eval grading, and nobody's asked for
MLflow/Neptune/Comet here. Wire a single, optional W&B hook into `run_heuristic()`,
gated by `WANDB_API_KEY` presence, same graceful-degradation pattern already used for
`ANTHROPIC_API_KEY` in `_try_generate_answer` (silently skip if absent, never crash the
eval run over a missing tracking key).

**Rough shape**: log `hit_rate`/`mean_reciprocal_rank`/`mean_answer_overlap` per run,
tagged with `data_sensitivity` (now that it exists) and whatever `run.py` already knows.
New `wandb` pyproject dep (optional-ish — same disclosure standard as `sentence-transformers`
in the prior plan: declare it plainly, don't hide the install cost).

**Status**: DONE. Added `wandb_api_key`/`wandb_project`/`data_sensitivity` fields to
`lg_agent/settings.py.jinja`, a `_try_log_to_wandb` private function + one call site in
`evals/pipelines/run.py` (same graceful-degradation shape as `_try_generate_answer`),
and `wandb>=0.18.0` to `pyproject.toml.jinja`. Verified: full render clean (no leftover
Jinja), `ruff check`/`format --check` clean, real `make corpus-ingest` +
`make eval-heuristic` run with no `WANDB_API_KEY` set — identical behavior to before
(no crash, same JSON output). **Not tested**: an actual W&B API call — no
`WANDB_API_KEY` available in this environment, same boundary class as the prior plan's
missing `ANTHROPIC_API_KEY`/`GOOGLE_API_KEY`. **Also not done**: `.env.example.jinja`'s
`WANDB_API_KEY=` documentation line — blocked by this environment's `.env*` permission
guard (same one hit during the prior akira phase). Add manually: one line next to the
existing `ANTHROPIC_API_KEY=` line.

## 2. ADK vs LangGraph toggle — bounded feature work ✓ DONE — 2026-07-14

**Gap**: `scaffold_full_project=true` unconditionally scaffolds all three example agents
(`lg_agent`, `rag_agent` — both LangGraph — and `adk_agent` — Google ADK) *and*
installs dependencies for all three regardless of which one you'll actually use.
Confirmed: `pyproject.toml.jinja` unconditionally pulls in `langgraph`, `langchain-*`,
**and** `google-adk`.

**Already flagged**: `puffin-integration/plan.md`'s "Open Questions" section explicitly
asked this and left it unresolved: *"Should rag_agent/adk_agent be independently
toggleable (like include_akira), or always bundled with scaffold_full_project as
currently planned?"*

**Rough shape**: a copier choice (e.g. `agent_framework`: `langgraph` / `adk` / `both`)
gating which agent dirs get moved into place during the `_scaffold/` → final-path `mv`
task (same staging mechanism `include_akira` already uses) and which framework deps
land in `pyproject.toml.jinja`. Comparable in size to one of the original six build
phases — real work, not a quick toggle.

**Open question for its own plan**: does `mcp_servers/<slug>`'s tool (currently backed
by `rag_agent` via HTTP) still make sense if `rag_agent` itself becomes optional?
Resolved: `rag_agent` never becomes optional (see Status below) — moot.

**Status**: DONE. Reframed as `primary_chat_agent` (`lg_agent`/`adk_agent`/`both`/`none`,
default `both`) per the conversation decision — `rag_agent` + `akira` (both LangGraph)
always ship as shared infra. Added the copier question + `_tasks` cleanup (mirrors
`include_akira`'s staged-path pattern), gated 3 pyproject deps
(`langchain-mcp-adapters`, `google-adk`, `mcp`) and the `Makefile`'s `lg-*`/`adk-*`
target blocks, fixed `akira`'s `SafeguardAgent`/`SchemaAgent` hardcoded agent
references (Jinja conditionals + a glob-based fix), and — the big one — generalized
`evals/pipelines/run.py` (renamed to `.jinja`) to grade every present retrieval
backend independently (`rag_agent` always, `lg_agent` conditionally), each with its
own `heuristic_results_{backend}.json`/report and W&B run tagged by backend. This
closes the pre-existing `rag_agent`/`adk_agent` eval-coverage gap `akira`'s own
`EvalAgent` had already flagged as known-and-accepted — it's no longer a gap even in
the default `both` config.

**Two real bugs caught only by testing all four configs for real** (render + ingest +
`make eval-heuristic` + `make test`, not just render success):
1. A Jinja/Python-f-string delimiter collision — renaming `run.py` → `run.py.jinja`
   broke the HTML report's inline `<style>` block, since Python's `{{ }}` (escaped
   literal brace in an f-string) is indistinguishable from Jinja's own `{{ }}` syntax.
   Fixed with a `{% raw %}...{% endraw %}` block around the CSS.
2. `tests/conftest.py`'s `wired_vectordb` fixture imported `agents.lg_agent.settings`
   unconditionally, breaking test collection whenever `lg_agent` is excluded — missed
   in the initial audit because it's outside `tests/unit/agents/` (which was already
   correctly gated). Fixed by moving the lg_agent-specific fixture into a new nested
   `tests/unit/agents/conftest.py` (removed automatically alongside that directory);
   root `conftest.py` keeps only the generic BM25-mechanics fixtures.
3. `agents/rag_agent/settings.py` never got the `wandb_api_key`/`wandb_project`/
   `data_sensitivity` fields added to `lg_agent`'s settings during the W&B work —
   caused an `AttributeError` crash the first time `_try_log_to_wandb` ran against
   the `rag_agent` backend in an `adk_agent`-only render. Fixed by adding the same
   3 fields and renaming to `settings.py.jinja` (needed Jinja substitution for
   `wandb_project`/`data_sensitivity`).

**Verified**: all 4 `primary_chat_agent` values render cleanly (no leftover Jinja,
correct dependency sets, correct agent directories present/absent), `ruff check`/
`format --check` clean on project source (excluding pre-existing vendored
`.claude/skills/mcp-builder/scripts/` formatting issues, out of scope), `make test`
passes on all 4 (36 tests for `both`/`lg_agent`, 17 for `adk_agent`/`none` — correctly
fewer since lg_agent's tests are absent), and — the concrete proof this actually
works — `make rag-corpus-ingest && make eval-heuristic` produces a real
`heuristic_results_rag_agent.json` in the `adk_agent`-only config, where the eval
suite previously would have crashed outright.

Also folded in, small and independent: `/sanyi init` suggested as a project-setup
next step in `_message_after_copy` and `project-genesis`'s Step 5 report.

## 3. Data pipeline / vector-backend choice — real feature work ✓ DONE — 2026-07-14

**Gap**: ingestion/retrieval mechanism is hardcoded per agent — DuckDB + BM25 FTS for
`lg_agent`, DuckDB + `sentence-transformers` embeddings for `rag_agent`. No copier
question makes this a real choice (batch vs. other, alternate vector backends).

**Status**: DONE. Extracted playground's real 3-backend factory pattern
(`rag/datastore/{factory,local,opensearch}.py` — memory/duckdb/opensearch behind one
entry point, `Retriever` protocol) into `rag_agent`, simplified to this template's
plain `(id, title, text, score)` tuple interface instead of playground's full
`Chunk`/`ChunkMetadata` schema. New `vector_backend` copier question
(`duckdb`/`memory`/`opensearch`, default `duckdb`). `vectorstore.py` → `.jinja`,
gained `MemoryVectorIndex` (dict + optional JSON snapshot for persistence across
restarts) and `OpenSearchVectorIndex` (HNSW kNN, lazy-imports `opensearch-py` so it's
never required unless actually used), both behind one `get_vector_index()` factory
(`@lru_cache` singleton, mirrors `get_embeddings()`'s own caching). Three call sites
(`nodes/retrieve.py`, `build_index.py`, `evals/pipelines/run.py.jinja`) simplified to
call the factory instead of instantiating `DuckDBVectorIndex` directly — none of them
need to know which backend is active. `opensearch-py` added to `pyproject.toml.jinja`
only when `vector_backend=opensearch`.

**Verified**: all three backends render cleanly (no leftover Jinja, opensearch-only
fields/dep present only in that config), `ruff check`/`format --check` clean (one
real line-length bug in the new file caught and fixed), full real
`make corpus-ingest && make rag-corpus-ingest && make eval-heuristic` chain passes
(hit_rate=1.0) for both `duckdb` and `memory` — including confirming the memory
backend's JSON snapshot actually persists 6 real records to disk. `opensearch` fails
gracefully with a real, clear `ConnectionError` (no cluster reachable in this
environment, no hang) rather than crashing unhelpfully or hanging indefinitely.

## 4. Backend language polyglot (TypeScript) ✓ DONE — 2026-07-14

**Gap**: `has_typescript` covered only the *frontend* case (hook checks assuming a TS
project already exists — no real backend scaffold, no eslint, no TS test runner).
Chosen scope (user decision): TypeScript backend specifically, not a generic
multi-language rearchitecture.

**Status**: DONE. New `primary_backend_language` (`python`/`typescript`/`both`, default
`python`) stages a real Node/TS backend service at `ts_project_root` (`package.json`,
`tsconfig.json`, `eslint.config.mjs` flat config, `jest.config.cjs`, a real Express
`/health` service split into `app.ts` (factory, testable) + `index.ts` (entrypoint)).
`has_typescript`'s default now derives from `primary_backend_language` but can still be
set independently for a frontend-only, layering-only TS project — decoupled from
whether this backend scaffold applies. New `ts_lint.sh.jinja` hook (the real
eslint-equivalent of `ts_quality.sh`'s ad-hoc checks) plus a TS test-gate mirroring the
existing inline Python pytest-before-commit gate in `settings.json.jinja` (not a
separate hook script, matching that precedent). New `Makefile` targets
(`ts-install`/`ts-lint`/`ts-typecheck`/`ts-test`/`ts-build`/`ts-dev`). Separately, new
`mcp_server_language` (`python`/`typescript`, independent toggle) stages a TS MCP server
from the already-existing-but-unused `node_mcp_server.md` reference doc, mirroring the
Python FastMCP server's exact `search_articles` tool/contract.

**Real source material used**: `github/_archived/sevdesk/va-agents`'s real
`eslint.config.mjs` (trimmed of Next.js-specific plugins) and Jest+ts-jest setup;
`template/.claude/skills/mcp-builder/reference/node_mcp_server.md`'s package.json/
tsconfig/tool-registration patterns.

**Three real bugs caught by actually running `npm install`/`lint`/`test`/`build`, not
just rendering**:
1. `package.json`'s `"type": "module"` (ESM) collided with `jest.config.js`'s
   CommonJS `module.exports` — `ReferenceError: module is not defined`. Fixed by
   renaming to `.cjs` (forces CommonJS regardless of package.json's type field).
2. Renaming alone didn't fix eslint — flat config needed an explicit
   `{ files: ["**/*.cjs"], languageOptions: { sourceType: "commonjs" } }` block, or
   eslint still parsed `.cjs` as ESM and flagged `module`/`require` as undefined.
3. `index.ts`'s `import.meta.url` entrypoint-check pattern broke ts-jest (`import.meta`
   not supported in ts-jest's hybrid module transform). Fixed by splitting into
   `app.ts` (exports `createApp()` only, what tests import) + `index.ts` (the
   entrypoint, never imported by tests) — simpler and avoids the ESM/CJS interop
   problem entirely rather than papering over it.

**Verified**: `primary_backend_language=typescript`/`both` render cleanly; real
`npm install && npm run lint && npm run typecheck && npm test && npm run build` all
pass for the TS backend service (including a real passing `/health` test via
`supertest`); real `npm install && npm run build` passes for the TS MCP server, and
booting it with real stdio JSON-RPC input (`initialize` + `tools/list`) returned the
correctly registered `search_articles` tool with its Zod-derived schema — a genuine
end-to-end MCP protocol handshake, not just a build check. `pre-commit run --all-files`
passes cleanly on a `both`-language render (ruff hooks correctly ignore TS files).

## 5. Classical ML/stats "labs" tier ✓ DONE — 2026-07-14

**Gap**: this template is entirely agentic-AI-shaped (LLM agents, RAG, evals against
a golden QA set). It had nothing for classical ML/stats work: baseline model
comparison (boosting vs. random forest), feature engineering/importance, cross-
validation, ML-interpretability plots, or A/B-test statistical techniques.

**Status**: DONE — full discovery scope, per your call to go broad rather than start
narrow. New `include_ml_labs` toggle (default `false` — large, opt-in, orthogonal to
the agentic-AI focus) stages a `labs/` tier with 6 modules, each ported from real
source and genericized (domain-specific logic rewritten, not copy-pasted):

| Module | Ported from | What changed |
|---|---|---|
| `regression/` | `NRR/src/models/model.py`+`plot.py` | RFE-based logistic regression, coefficient tables, significance plots — stripped the food/menstrual-cycle domain logic, kept the statistical core |
| `timeseries/` | `atlas/evals/arima.py` + `core/preprocessing/preprocessing.py` | ARIMAForecaster w/ full assumption diagnostics — ported mostly faithfully (already generic); trimmed the polars-based `Preprocessor`/`fill_gaps` DataFrame wrapper (pipeline glue, not reusable core) |
| `stats_testing/` | sevdesk's real Dec-2025 A/B-test notebook | Power analysis, Wilson CI, Mann-Whitney U, bootstrap Cliff's delta — de-Germanized, hardcoded CSV paths removed |
| `feature_engineering/` | `atlas/core/preprocessing/features.py` | Lag/rolling/EWM/calendar/Fourier builders **rewritten polars→pandas**, vectorized via `groupby().shift()`/`.rolling()` instead of the original's manual per-series loops (faster, not just ported); mutual-info/correlation/permutation importance ported as-is (already numpy-only); dropped `add_company_level_features` (cash-flow-specific) |
| `model_comparison/` | `lebanese-blonde/src/models.py` (real, deployed LightGBM scorecard) | `TabularPreprocessor` genericized from `PreprocessData` (feature lists as constructor params, not a dataset-specific import); new `compare_classifiers()` — the actual "boosting vs. random forest baseline" harness you asked for |
| `clustering/` | `listen-wiseer/src/recommend/modules/clustering.py` | GMM soft-clustering pattern genericized (dropped hardcoded Spotify audio-feature/key-mode columns for constructor-supplied feature lists); `classifiers.py` (532 lines, playlist-reranking-specific) explicitly NOT ported — too task-specific, already covered generically by `model_comparison` |

New deps (only when `include_ml_labs`): `scikit-learn`, `statsmodels`, `scipy`, `pandas`,
`matplotlib`, `lightgbm`, `statsforecast`. `labs/README.md.jinja` documents a
discovery→delivery workflow (discover → baseline → explain → validate → forecast →
measure) modeled on `atlas/CLAUDE.md`'s layout documentation style.

**Four real bugs caught by actually running the full chain (render → `uv sync` →
`ruff` → `pytest` → `pyright`), not just writing code**:
1. `labs/README.md` used `{{ eval_root }}`/`{{ source_root }}` template variables
   without the `.jinja` suffix — silently would have shipped unrendered `{{ }}` into
   every generated project.
2. Mistakenly added `tests/unit/labs/__init__.py` (the established convention —
   confirmed against `tests/unit/agents/` — has no `__init__.py` in test dirs) —
   broke pytest's import resolution for the `labs` package entirely.
3. `statsmodels`' `conf_int()` returns a plain `ndarray` (not a DataFrame) when fit on
   a raw numpy array rather than a pandas Series — `ARIMAForecaster.predict()` crashed
   with `AttributeError: 'ndarray' object has no attribute 'iloc'` the first time it
   actually ran end-to-end.
4. The `labs/` staging cleanup task (`rm -rf _scaffold/labs` when `include_ml_labs=false`)
   removes the *entire* top-level staging directory, which would make the big
   unconditional `mv` task fail on a missing path if `labs` were added to that list
   directly — caught before it ever hit a real render, by reasoning through the same
   staging-order bug class the `ts_project_root` toggle had already surfaced; fixed
   with a separate conditional `mv`, same pattern as that one.

**Also caught and fixed**: 38 real `pyright` errors introduced into a previously
100%-clean baseline (`core`/`evals` remain 0 errors) — almost all third-party stub
imprecision (numpy/scipy/statsmodels/matplotlib/sklearn stubs disagreeing with real
runtime types, e.g. `mannwhitneyu`'s result stub not exposing `.statistic`/`.pvalue`,
`adfuller`'s overloads being unresolvable from kwargs alone). Fixed the one genuine
issue for real (`plt.Figure`/`plt.Rectangle` aren't actual public exports —
switched to `matplotlib.figure.Figure`/`matplotlib.patches.Rectangle`); the rest are
narrow, individually-commented `# type: ignore[...]` at the exact stub-gap lines.
Down to 0 errors, all 66 unit tests still passing throughout.

**Verified**: `include_ml_labs=true`/`false` both render cleanly (no leftover Jinja,
correct dir presence/absence), `ruff check`/`format --check` clean, `pyright labs`
clean (0 errors), all 66 unit tests pass (30 in `labs/` alone) against real data
(`sklearn`'s `breast_cancer`/`make_blobs`, numpy-generated trending series) — every
module has at least one assertion on a real fitted-model property, not just "it ran
without crashing."

## 6. Repo-root + generated-project scaffolding parity with the old ds template ✓ DONE — 2026-07-14

**Gap, confirmed by direct comparison**:
- `ai-project-template`'s own repo root (vs. `ds-python-project-template`'s root:
  `.github`, `.vscode`, `.gitignore`, `.pre-commit-config.yaml`, `renovate.json`,
  `pixi.lock`) was missing a `.gitignore` — fixed immediately (2026-07-14, trivial,
  no design decision needed) since its absence is exactly what let a failed test
  render (`Workspace/`, since deleted) sit around as untracked debris. Still missing,
  not yet scoped: `.github/` CI that actually tests the template renders correctly
  (bigger, valuable), `.pre-commit-config.yaml`/`renovate.json` for the template
  repo itself (lower priority — the template repo has no runtime deps of its own).
- Generated project (`_scaffold/`) vs. `templates/data_science/`: has `.github`,
  `project_init.sh` (single script vs. the old template's `.project_setup_scripts/`
  dir — a naming/shape difference, not a gap), `.vscode`, `configs`, `data`,
  `infrastructure` (named `infra` in the old template — cosmetic), `nbks`, `src`,
  `tests`, `.gitignore`, `pyproject.toml`, `README.md` — all present. Missing:
  **`.pre-commit-config.yaml`** (real gap — today enforcement is 100% Claude-session
  hooks; nothing enforces anything for a human dev without Claude Code, or in CI
  outside the `.claude/hooks/*.sh` scripts) and **`renovate.json`** (real, cheap,
  valuable gap — this project has several fast-moving AI framework deps —
  `langgraph`, `google-adk`, `wandb` — that benefit from automated update PRs).
  `docs/` (architecture diagrams, env-setup screenshots) is present in the old
  template but is a nice-to-have, not a functional gap.

**Status**: DONE. Added `template/_scaffold/.pre-commit-config.yaml` (ruff-pre-commit
+ standard hygiene hooks, `exclude: ^(\.claude|\.agents)/` to match the Makefile's
`LINT_PATHS` scoping — one `[tool.ruff]` source of truth, two enforcement paths) and
`template/_scaffold/renovate.json` (`config:recommended` + a `packageRules` entry
holding `langgraph`/`langchain-core`/`langchain-mcp-adapters`/`google-adk`/`wandb`
back from automerge). Both wired into the `_tasks` `mv` list (missed on the first
pass — caught immediately by rendering and checking for the files, not just render
success). Added `ai-project-template/.github/workflows/test-render.yml` — a real CI
matrix (defaults, layering-only, each `primary_chat_agent` value) automating this
session's manual verification loop.

**A real bug caught by actually running `pre-commit run --all-files`, not just
rendering**: without the `exclude` pattern, `ruff`'s pre-commit hook ran repo-wide
by default and failed on `.claude/skills/mcp-builder/scripts/` (vendored reference
material the Makefile's own `lint` target already deliberately excludes) — fixed.
Verified: `pre-commit run --all-files` passes clean on a fresh render, layering-only
mode renders with neither file present (correct — they belong to the full-project
tier), `renovate.json` is valid JSON.

## Sequencing

All six items done as of 2026-07-14 (#1 W&B, #2 primary_chat_agent + eval
generalization, #6 pre-commit/renovate/CI, #3 vector_backend, #4 TypeScript
backend + MCP server language, #5 classical ML/stats labs tier) — implemented in
that order, each with its own review checkpoint and real end-to-end verification
(render + install real deps + run real tests), not just code review. No open
backlog items remain from this pass.
