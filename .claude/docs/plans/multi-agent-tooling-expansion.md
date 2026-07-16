# Plan: close the shared tooling gaps for project-mgmt-ai + grant-fundraising-ai

Date: 2026-07-14 (revised 2026-07-14 — scope expanded, see below)
Context: see `../research/multi-agent-tooling-parity.md` for the full gap matrix. Two
projects are actually being built on `ai-project-template`: project-mgmt-ai and
grant-fundraising-ai (nyc-dssg, not yet scaffolded as a repo). Both propose tool
stacks only partially covered by the template today. Since both are real, committed
builds — not speculative — this plan scopes **all** the gaps identified in the
research doc as template additions, not just the ones shared by both projects. Same
discipline as the prior 6-item backlog throughout: each phase gets its own review
checkpoint and real end-to-end verification, not just code review.

**Revision note**: the original version of this plan deferred the gaps unique to a
single project (external SaaS connectors, meeting-transcription ingestion, AutoGen,
LlamaIndex, Composio, GPT-Researcher/Browser-use, Ragas, Promptfoo) on the assumption
they might not be needed yet. That assumption no longer holds — both repos are being
built, so those are real requirements now. They're scoped below as Phase 4
(project-mgmt-ai-specific) and Phase 5 (grant-fundraising-ai-specific).

## Why this order

The three gaps shared by both projects (Postgres/Supabase, n8n-callability, CrewAI)
still go first — highest-leverage (build once, both projects benefit), and Phase 3's
CrewAI work builds the staged-agent-tree + eval-wiring + per-service Docker pattern
that Phase 5's AutoGen addition then reuses directly rather than inventing again.
Ordered cheapest/most-grounded → most architecturally significant:

1. Postgres/pgvector — two real stubs already exist to finish (not new subsystems)
2. n8n-callable contract — no existing pattern, but small in scope (an endpoint
   convention + doc, not new infra)
3. CrewAI — no existing pattern, and the largest of the three (a second orchestration
   framework, comparable in size to this session's TypeScript-backend item)
4. project-mgmt-ai-specific integrations (Calendar/Eventbrite/LinkedIn/Canva,
   meeting-transcription ingestion) — real requirements for that project, independent
   of phases 1-3, gated by their own toggles
5. grant-fundraising-ai-specific integrations (AutoGen, LlamaIndex, Composio,
   GPT-Researcher/Browser-use, Ragas, Promptfoo, Pydantic-AI) — largest single phase;
   several sub-items reuse Phase 3's plumbing directly. Since grant-fundraising-ai
   isn't scaffolded yet, this phase's toggles land in the template now but get
   exercised for real once that repo is created from it.

**Execution-order note (2026-07-14)**: after Phases 1-2 landed, the user asked to
do Phase 4 and the non-CrewAI-dependent parts of Phase 5 before Phase 3, since
Phase 3 (CrewAI) is the largest of the three shared-gap phases and Phase 4 has no
dependency on it. Actual execution order: 1 → 2 → 4 → 5 (minus AutoGen, which
explicitly reuses Phase 3's staged-agent-tree/eval-wiring/Docker pattern and stays
blocked on it) → 3 (CrewAI) + Phase 5's AutoGen sub-item together, since AutoGen's
whole rationale is "apply Phase 3's already-proven pattern a second time."

## Phase 1 — Postgres/pgvector backend (finish two existing stubs) ✓ DONE — 2026-07-14

**Gap**: `vector_backend` supports `duckdb`/`memory`/`opensearch` but not
`postgres`/`supabase`. `agents/lg_agent/checkpointer.py::get_checkpointer()` already
stubs a `PostgresSaver` branch that raises `NotImplementedError`.

**Design**:
- Add `postgres` as a fourth `vector_backend` choice. New `PostgresVectorIndex` in
  `vectorstore.py.jinja`, same shape as `OpenSearchVectorIndex` (lazy-imports
  `psycopg`/`pgvector`, same `(id, title, text, score)` tuple return, registered in
  `get_vector_index()`'s existing factory — no call-site changes needed, same as when
  OpenSearch was added).
- Finish `get_checkpointer()`'s `PostgresSaver` branch for real (currently a documented
  but unimplemented stub) — wire it to a `POSTGRES_URL`/`SUPABASE_DB_URL` setting,
  following `.agents/skills/langgraph-persistence/SKILL.md`'s documented setup code.
- New copier question or reuse `vector_backend`'s existing `postgres` value to also
  gate whether `lg_checkpointer` defaults to `postgres` — keep these two independently
  toggleable (a project might want Postgres vectors but in-memory checkpointing, or
  vice versa) rather than coupling them, matching the template's existing philosophy
  of orthogonal toggles (`primary_chat_agent` vs. `vector_backend` are already
  independent).
- `pyproject.toml.jinja`: add `psycopg[binary]`/`pgvector` (vector backend) and
  `langgraph-checkpoint-postgres` (checkpointer) as conditional deps, same pattern as
  `opensearch-py`.
- Document the "Supabase is just Postgres+pgvector" framing explicitly in the README —
  Supabase requires no separate SDK for this use case, just its connection string.

**Files**: `vectorstore.py.jinja`, `checkpointer.py.jinja` (rename from `.py`),
`copier.yaml` (new choice + settings), `pyproject.toml.jinja`, README.

**Verification**: same bar as the OpenSearch item — render, confirm import/construction
succeeds and fails gracefully with a clear connection error when no Postgres is
reachable in this environment (don't attempt to stand up a real Postgres/Supabase
instance here); if a local Postgres is available via Docker, run the real ingest+eval
chain against it as a stronger check.

**Status**: DONE. Added `PostgresVectorIndex` to `vectorstore.py.jinja` (lazy
table creation once the embedding dimension is known, same shape as
`OpenSearchVectorIndex`'s `_ensure_index`; table/column names go through
`psycopg.sql.Identifier` rather than f-string interpolation even though `table`
only ever comes from trusted settings — cheap to do correctly). Both
`checkpointer.py` factories (`lg_agent`, `rag_agent`) now implement the
previously-stubbed `PostgresSaver` branch for real, `@lru_cache`-memoized (same
singleton shape as `get_vector_index()`/`get_embeddings()`), documented tradeoff
noted in the docstring (`PostgresSaver`'s async methods run sync psycopg calls via
a thread-pool executor, not native async — `AsyncPostgresSaver` is the upgrade
path if that becomes a bottleneck). New `enable_postgres_checkpointer` toggle,
`postgres_dsn`/`postgres_table` settings, conditional `psycopg[binary]`/`pgvector`/
`langgraph-checkpoint-postgres` deps.

**One real bug caught only by running `make test`, not just rendering**: the
original design made `enable_postgres_checkpointer=true` flip the *runtime
default* of `lg_checkpointer`/`rag_checkpointer` to `"postgres"`. Unlike
`vector_backend` (consumed lazily, per-call, via `get_vector_index()`), the
checkpointer is consumed *eagerly* at graph-compile time (`graph.py`'s
module-level `build_graph()` call) — so this default made every test that merely
imports `main.py` try to open a real Postgres connection, failing 4/36 tests with
a raw `psycopg.OperationalError` in a fresh render with no Postgres running.
Fixed by keeping the runtime default at `"memory"` unconditionally — the toggle
now only controls whether the dependency + working code path exist; opting into
`postgres` at runtime is an explicit `LG_CHECKPOINTER=postgres` (+ `POSTGRES_DSN`)
env var once a database is actually reachable, matching every other
optional-backend's safe-default precedent in this template.

**Verified**: both `vector_backend=postgres` and the default `duckdb` configs
render cleanly (no leftover Jinja beyond the pre-existing, intentional f-string
CSS braces in the eval report), `ruff check`/`format --check` clean on both,
`make test` passes 36/36 on both after the fix (was 32/36 on postgres before the
fix), the default `duckdb` config's full `corpus-ingest`/`rag-corpus-ingest`/
`eval-heuristic` chain still passes (hit_rate=1.0 — no regression from adding the
fourth backend). Both the vector index and the checkpointer fail fast with a
clear `psycopg.OperationalError` (not a hang, not a confusing traceback) when
pointed at an unreachable Postgres via explicit env-var opt-in — matching the
established environment-boundary pattern used elsewhere for untestable
external services. Docker was available but its daemon wasn't running in this
environment, so the stronger "real local Postgres" check wasn't performed;
pyright was checked too — the postgres branch introduces zero *new* errors
beyond the pre-existing, already-accepted class (unresolved imports for
whichever backend's optional dependency isn't installed for the selected
config — the same tradeoff already established by `opensearch-py`).

## Phase 2 — n8n-callable contract ✓ DONE — 2026-07-14

**Gap**: no agent exposes a documented, stable HTTP contract for an external workflow
tool (n8n) to call, and no signed-webhook receiver pattern exists for n8n to call back
into the project.

**Design** (deliberately NOT installing or vendoring n8n itself — it's an external
service):
- Document (new `.agents/skills/n8n-integration/SKILL.md` or a README section) the
  existing agent HTTP endpoints (`lg_agent`/`adk_agent`/`rag_agent` already expose
  `/chat` or `/api/v1/retrieval`-shaped routes) as n8n HTTP-Request-node-callable
  contracts — API-key-header auth, request/response JSON shape, error semantics.
- Add one new generic `webhooks/inbound.py`-style route (behind a required shared-secret
  header, HMAC-verified) as the "n8n calls back into us" direction — e.g. for
  "workflow finished, update this record" callbacks. Keep it generic (a typed payload +
  a pluggable handler function), not n8n-specific business logic.
- No new copier toggle needed if this ships as part of `scaffold_full_project`'s
  existing HTTP surface — evaluate during implementation whether it warrants its own
  `include_n8n_webhook` gate (likely yes, since not every project needs an inbound
  webhook receiver).

**Files**: new skill/doc, new webhook route + settings (shared-secret env var),
`copier.yaml` (possible new toggle), README.

**Verification**: real HTTP round-trip against the rendered project (curl with a valid
vs. invalid HMAC signature — confirm 401 on the latter), not just code review. n8n
itself isn't available in this environment to test against; verify the contract is
n8n-compatible by matching n8n's documented HTTP Request / Webhook node payload shapes
rather than a live n8n instance.

**Status**: DONE, and scoped smaller than the original design once implementation
started: rather than retrofitting `X-API-Key` auth onto `lg_agent`/`rag_agent`
(adk_agent's gateway already has it), documented the current, real state as-is
(a real gap worth flagging in the README, not silently inventing a new auth
layer across 3 agents in this phase) and focused effort on the one thing with
no existing pattern at all — the inbound direction. New
`{{ source_root }}/integrations/` package (`settings.py` — a shared
`IntegrationSettings` class separate from each agent's own, since these routes
aren't agent-specific; `n8n_webhook.py` — the HMAC-verified route + pluggable
`EVENT_HANDLERS` dispatch). Mounted into all three agents' FastAPI apps
(`lg_agent`, `rag_agent`, `adk_agent/gateway`) via a `try/except ImportError`
pattern rather than converting any `main.py` to `.jinja` — when
`include_n8n_webhook=false`, `_tasks` removes `integrations/` entirely, the
import fails, and the `except` silently skips mounting. No agent's `main.py`
needed Jinja conditionals at all. New `include_n8n_webhook` toggle (default
`false`), README "Integrations" section documenting both directions.

**Verified**: both `include_n8n_webhook=true`/`false` render cleanly (`integrations/`
present/absent correctly, no leftover Jinja), `ruff check` clean (`format --check`
caught one real formatting issue in the new file, fixed by running `ruff format`
inside the rendered project and copying the corrected file back — not by guessing
at formatting), `make test` passes 36/36 on the `true` config. Real end-to-end
HTTP verification: booted the actual FastAPI app with `uvicorn`, then `curl`'d
`POST /webhooks/n8n` three ways — valid HMAC signature → `200` and the example
handler actually fired (confirmed via server log: `Received 'example.event'
webhook: {'foo': 'bar'}`), invalid signature → `401`, missing signature header →
`401`. A genuine protocol-level round-trip, not a mocked unit test.

## Phase 3 — CrewAI as a selectable orchestration framework

**STALE — 2026-07-15, not being built.** This phase's whole rationale was
"both proposals actually want CrewAI" (project-mgmt-ai's and
grant-fundraising-ai's original README proposals). That premise no longer
holds: `project-mgmt-ai` is now directed at **LangGraph**, not CrewAI (per
Ramsey's direction in the same session that produced
`ai-project-template/.claude/docs/plans/vercel-native-ts-agent-scaffold.md`),
and `dssg/roadmap.md` §3's revised recommendation (informed by real
hackathon output, not proposal text) is explicit that CrewAI/LangGraph
"appear *only* in proposal documents org-wide... never in curriculum or
shipped cohort work" — what's actually taught is n8n (no-code) and Google
ADK (pro-code), and what cohort teams actually ship is plain Python or n8n,
no multi-agent-crew framework at all. Building CrewAI support now would be
template infrastructure with no confirmed consumer. Left unimplemented and
documented here rather than silently dropped — revisit if a real, confirmed
CrewAI need surfaces later (not from a proposal doc alone).

**Gap** (as originally scoped, now stale): `primary_chat_agent` only offers
`lg_agent`/`adk_agent`/`both`/`none`. No role-based multi-agent-crew
framework exists.

**Design** (largest phase — budget like the TypeScript-backend item, its own
mid-phase review checkpoint):
- Extend `primary_chat_agent`'s choices to include `crew_agent` (and update `both` to
  mean "the two you'd realistically pair," clarified during implementation — likely
  `lg_agent`+`crew_agent` since ADK and CrewAI solving the same role-based-team problem
  side by side is less obviously useful than LangGraph-graph + CrewAI-crew for
  different jobs).
- New staged `_scaffold/{{ source_root }}/agents/crew_agent/` tree: `crew.py` (Crew +
  Agent + Task definitions — Researcher/Writer/Editor roles, matching the shape both
  proposals actually want), `settings.py.jinja`, `main.py` (FastAPI wrapper exposing
  the same `/chat`-shaped contract other agents use, so it's n8n-callable via Phase 2's
  contract and gradeable by the existing eval suite without special-casing).
- `evals/pipelines/run.py.jinja`: extend the "grade every present retrieval backend
  independently" generalization (already built this session for `lg_agent`/`rag_agent`)
  to also grade `crew_agent` when present — same pattern, not a new one.
- Generalize `docker-compose.yml`/`Dockerfile` beyond `lg_agent`-only (real gap
  surfaced by this research) so `crew_agent` (and any future service) gets the same
  per-service Dockerfile pattern rather than a one-off.
- `pyproject.toml.jinja`: `crewai` as a conditional dep.

**Files**: `copier.yaml`, new `agents/crew_agent/` tree, `evals/pipelines/run.py.jinja`,
`infrastructure/containers/` (generalize), `Makefile.jinja` (crew-* targets mirroring
`lg-*`/`adk-*`), pyproject, README.

**Verification**: same bar as `primary_chat_agent`'s original build — render each
config, `uv sync`, `make test`, `make crew-up` + a real chat turn, `make eval-heuristic`
producing a real `heuristic_results_crew_agent.json`.

## Phase 4 — project-mgmt-ai-specific integrations ✓ DONE — 2026-07-14

**Gap**: Google Calendar API, Eventbrite API, LinkedIn API, Canva API (all real,
unique to project-mgmt-ai), plus meeting-transcription ingestion (Granola/Fireflies).
No connector pattern or transcript-to-action pipeline exists anywhere in the template.

**Design**:
- First, one general "call an external REST API with an API key" connector pattern —
  generalizes the MCP server's existing `httpx` + `try/except HTTPError` shape (already
  proven, not invented) into a documented module convention: typed request/response
  Pydantic models (matching the "Pydantic at boundaries" hard rule), graceful
  degradation when a key/token is absent (same pattern as `_try_generate_answer`/
  `_try_log_to_wandb`), one client class per external service.
- `integrations/google_calendar.py`: OAuth2 (user-delegated, since this is scheduling
  on a human coordinator's behalf, not a service account) — `create_event`,
  `list_events`, `find_availability`. This is the "autonomous scheduling" deliverable
  the proposal's Sprint 3 calls for.
- `integrations/eventbrite.py`, `integrations/linkedin.py`, `integrations/canva.py`:
  each a thin client following the same connector pattern — `publish_event`,
  `post_update`, `generate_asset` respectively. Gated by one `include_marketing_integrations`
  toggle (bundled, since Sprint 6 in the proposal treats them as one "marketing
  automation" unit) rather than four separate toggles.
- `integrations/meeting_intelligence.py`: accepts a transcript (webhook from
  Granola/Fireflies, or manual upload), runs an LLM extraction pass into a structured
  Pydantic schema (action items, owners, deadlines, decisions) — the proposal's
  Sprint 1-2 ("Meeting Intelligence" + "Action Management") deliverable. Feeds
  extracted actions into whichever agent framework is active (`lg_agent`/`crew_agent`)
  via the same internal call shape, not a separate storage layer.
- New copier toggles: `include_calendar_integration`, `include_marketing_integrations`,
  `include_meeting_intelligence` — independent of each other and of
  `primary_chat_agent`/`vector_backend`, following the template's existing orthogonal-
  toggle philosophy.

**Files**: new `integrations/` tree (staged like `agents/`), `copier.yaml` (3 new
toggles), `pyproject.toml.jinja` (conditional deps: `google-api-python-client`,
`google-auth-oauthlib`), settings/env-var additions, README.

**Verification**: real construction/import for each client with graceful, clear
failure when credentials are absent (same environment-boundary pattern as
`ANTHROPIC_API_KEY`/`WANDB_API_KEY` elsewhere — don't attempt live OAuth flows or
real API calls to Google/Eventbrite/LinkedIn/Canva in this environment). The
meeting-transcription extraction pass can be verified for real against a sample
transcript fixture (no external API needed — just the LLM call, same boundary as
other agent calls already tested this session).

**Status**: DONE, one design change from the original sketch: rather than
retrofitting `X-API-Key` auth across agents (a Phase 2 decision already made —
`adk_agent`'s gateway has it, `lg_agent`/`rag_agent` don't yet, documented as a
known gap), effort went into the four real connectors + the extraction module.
New `integrations/google_calendar.py` (`GoogleCalendarClient` — list/create
events, find-availability gap-scan; uses a pre-obtained OAuth2 refresh token,
not an interactive consent flow, since automating a real Google OAuth screen
isn't something a starter template can do — documented as a one-time manual
setup step in the module's docstring instead of half-implementing it).
`integrations/{eventbrite,linkedin,canva}.py` — three thin `httpx` clients
(Eventbrite's create-then-publish two-step flow, LinkedIn's UGC Posts API,
Canva's Autofill API), one shared `include_marketing_integrations` toggle since
the proposal treats them as one "marketing automation" unit, not three separate
choices. `integrations/meeting_intelligence.py` — `extract_action_items()`, one
LLM call producing a structured `MeetingExtraction` (Pydantic: summary,
decisions, action items with owner/deadline) via a new `integrations/clients/llm.py`
factory (needed so the existing `sdk_lint.sh` hook's "only `clients/llm.py` may
instantiate `anthropic.Anthropic()` directly" rule is satisfied here too, not
just inside each agent). Three new independent toggles
(`include_calendar_integration`, `include_marketing_integrations`,
`include_meeting_intelligence`) plus `include_n8n_webhook` from Phase 2 are all
independently removable from `integrations/` — not a blanket `rm -rf` tied to
one toggle, which would delete modules gated by the *other* toggles (the same
staging-order bug class caught during the `labs`/`ts_project_root` work) — with
a final catch-all task removing the whole (now-empty) package if none of the
four are enabled.

**Verified**: all three toggle states (all four on, all off, and a "calendar
only" mix — the specific case that would have caught the blanket-rm-rf bug if
I'd written it that way) render cleanly, correct files present/absent in each.
`ruff check`/`format --check` clean (one real `E501` + one formatting issue in
the new test file, fixed inside the rendered project and copied back). `make
test` passes 38/38 on the all-on config (36 existing + 2 new), 36/36 on the
all-off config. All four connector classes (`GoogleCalendarClient`,
`EventbriteClient`, `LinkedInClient`, `CanvaClient`) raise a clear
`RuntimeError` naming the missing env var when constructed without credentials
— verified by real construction attempts, not just reading the code.
`extract_action_items()` has a real pytest test with a mocked Anthropic
response verifying the actual JSON-parsing/Pydantic-validation path works (not
just its own graceful-failure path), plus a second test confirming the clear
error without `ANTHROPIC_API_KEY`. `pyright` introduces zero *new* errors in
the calendar-enabled config (the `google-api-python-client` import resolves
since the dependency is actually installed there); in configs with
`include_n8n_webhook=false` (the default), the `try/except ImportError` mount
pattern in each agent's `main.py` does add 3 new `reportMissingImports`
warnings — pyright can't see that the import is deliberately guarded at
runtime — but this is the same accepted tradeoff class already established by
the opensearch/postgres backends (optional-dependency code coexisting
unconditionally in a file that's only sometimes fully installed), not a new
problem, and left as-is rather than adding narrow `# type: ignore` noise to
something the try/except already self-documents.

## Phase 5 — grant-fundraising-ai-specific integrations

**Partially stale — 2026-07-15.** This phase bundles seven independent
sub-items. Only the **AutoGen** sub-item depends on Phase 3 (CrewAI), which
is now marked stale/not-being-built (see Phase 3's note above) — AutoGen
inherits the same problem, since its whole design was "apply Phase 3's
already-proven pattern a second time," and there's no more real-usage
confirmation for AutoGen specifically than there was for CrewAI. The other
six sub-items (LlamaIndex, Composio, GPT-Researcher/Browser-use, Ragas,
Promptfoo, Pydantic-AI) don't depend on Phase 3 at all and aren't affected
by this — they remain open for the unrelated reason that
`grant-fundraising-ai` isn't scaffolded yet, not because of the CrewAI
question. If this phase is picked up later, treat AutoGen as blocked
pending a real confirmed need, and the other six as independently
startable.

**Gap** (as originally scoped): AutoGen, LlamaIndex, Composio,
GPT-Researcher/Browser-use, Ragas, Promptfoo, Pydantic-AI — all unique to
grant-fundraising-ai (repo not yet scaffolded). Largest single phase;
AutoGen alone builds directly on Phase 3's CrewAI plumbing (see above).

**Design**:
- **AutoGen** (blocked — see note above): extend the orchestration-framework choice (from Phase 3) with an
  `autogen_agent` value, reusing the exact staged-agent-tree + `/chat`-contract-wrapper
  + eval-suite-generalization + per-service-Dockerfile pattern Phase 3 built for
  `crew_agent` — this is "apply an already-proven pattern a second time," not new
  design work.
- **LlamaIndex**: an alternative RAG implementation for `rag_agent` — new
  `rag_framework` toggle (`native`/`llamaindex`), independent of `vector_backend`
  (LlamaIndex is a retrieval/indexing *framework* layer; `vector_backend` is the
  storage layer underneath it — confirm during implementation whether LlamaIndex's
  own store connectors can point at the same duckdb/postgres/opensearch backends
  already built, to avoid a second storage abstraction).
- **Composio**: tool-execution SaaS — wired as one more connector following Phase 4's
  general external-API pattern, exposed as a tool any agent framework (LangGraph,
  CrewAI, AutoGen) can call — not a deep framework-level integration.
- **GPT-Researcher / Browser-use**: web-research tool functions pluggable into
  whichever orchestration framework is active (LangGraph tool node / CrewAI tool /
  AutoGen tool), covering the proposal's "funder history and past grantees" research
  need. One shared tool implementation, framework-specific thin adapters.
- **Ragas**: added as one more grader inside `evals/pipelines/run.py.jinja`'s existing
  grader-registration shape (already proven this session to support multiple graders
  per backend) — `include_ragas_grader` toggle, conditional `ragas` dep, runs
  alongside the existing heuristic/W&B graders, not replacing them.
- **Promptfoo**: a separate CLI/config-driven eval tool (not Python-native) — ships as
  an optional `promptfoo.config.yaml.jinja` + a `promptfoo-eval` Makefile target
  (`npx promptfoo eval`), run alongside the Python eval suite.
- **Pydantic-AI**: open question to resolve at implementation time — offer as an
  additional selectable orchestration framework (alongside LangGraph/ADK/CrewAI/
  AutoGen), or treat it as reinforcement of the existing "Pydantic at boundaries"
  convention rather than a new framework choice. Don't guess now; decide once this
  phase starts, based on what grant-fundraising-ai's actual agents need.

**Files**: `copier.yaml` (new orchestration value + `rag_framework`/`include_ragas_grader`
toggles), new `agents/autogen_agent/` tree, `rag_agent` LlamaIndex variant, new
`integrations/composio.py` + research-tool modules, `evals/pipelines/run.py.jinja`
(Ragas grader), `promptfoo.config.yaml.jinja` + Makefile target, pyproject
(conditional deps for all of the above), README.

**Verification**: same bar as Phase 3 for `autogen_agent` (render, `uv sync`, real
chat turn, real eval run). For LlamaIndex: real ingest + retrieval round-trip against
whichever `vector_backend` is active. For Ragas: a real grader run against the
existing golden-QA fixture data. For Composio/GPT-Researcher/Browser-use: same
graceful-degradation-without-credentials verification as Phase 4's connectors. Given
grant-fundraising-ai doesn't exist yet, the strongest real-world verification of this
phase happens once that repo is actually scaffolded from the template — flag that as
a follow-up check, not a substitute for verifying in this environment first.

## Sequencing

Phase 1 (Postgres/pgvector) → Phase 2 (n8n-callable contract) → Phase 3 (CrewAI, its
own internal checkpoint) → Phase 4 (project-mgmt-ai integrations) → Phase 5
(grant-fundraising-ai integrations, its own internal checkpoint per sub-item given
its size). Each phase implemented and verified (render + real deps + real tests, not
just code review) before moving to the next, matching the discipline established
across the prior 6-item backlog.
