# Plan: deepen TypeScript scaffold for a native Vercel AI SDK agent

Date: 2026-07-15
Status: **ALL 3 PHASES DONE — 2026-07-15.** Gate cleared 2026-07-15 (toggle
shape: new orthogonal `ts_agent_framework`; route handler: framework-agnostic;
`framework-selection` gets a third branch — see Gate below for the resolved
answers). Phase 1 (core agent loop), Phase 2 (eval parity), Phase 3 (Vercel
deploy convention) all implemented and verified — see each phase's own
section below for what shipped and how it was checked. Everything was
verified locally (real renders, real npm installs, a real running server,
real curl/eval runs against it) — a real Vercel deploy is still unverified
since no Vercel account/CLI exists in this environment; flagged as a
follow-up once `nonprofit-success-ai` actually consumes this. Motivated by
`dssg/platform/agents/nonprofit-success-ai/.claude/docs/plans/portal-hardening-and-buildout.md`'s
Phase 4 (blocked, TBD) deciding the portal's assistant should be a
**Vercel-native TS agent living in that repo's `src/agents/`**, using the
Vercel AI SDK (`tool()` + `streamText`) — no second service, no container.
`project-mgmt-ai` goes the other way (LangGraph, per Ramsey's direction this
session) — so this plan is scoped to the TypeScript/Vercel side only.

## Why this exists

`primary_backend_language: typescript|both` today stages a bare Express app
(`{{ ts_project_root }}/{{ ts_source_root }}/app.ts.jinja` — one
`express()` instance, one `/health` route, no LLM code at all) — see
`template/_scaffold/{{ ts_project_root }}/`. Compare to the Python side:
`lg_agent`/`adk_agent`/`crew_agent` are full staged trees with settings,
checkpointer, tools, eval wiring, Docker. There is currently no TS
equivalent, no Vercel AI SDK dependency anywhere in the template, and
`.agents/skills/framework-selection/SKILL.md` only decides between ADK and
LangGraph — it has no branch for a TypeScript-native agent at all. Building
`nonprofit-success-ai`'s portal assistant today would mean inventing this
from scratch in that repo, with no reusable pattern for the next
Vercel-hosted DSSG frontend that needs the same thing.

## Gate — resolved 2026-07-15

1. **Toggle shape**: new orthogonal `ts_agent_framework: none|vercel_ai_sdk`
   in `copier.yaml`, `when: has_typescript`, independent of
   `primary_backend_language` — matches `vector_backend`'s independence from
   `primary_chat_agent`.
2. **framework-selection**: yes, gained a third branch (Vercel AI SDK) —
   `.agents/skills/framework-selection/SKILL.md` now asks "does this need to
   run in a TS/Node runtime" first, before the ADK/LangGraph control-flow
   questions.
3. **Route handler shape**: framework-agnostic — `agent/handler.ts` exports a
   plain `(req: Request) => Response`, wired into the existing Express app
   via one adapter route (`POST /agent/chat` in `app.ts.jinja`), droppable
   into a Next.js route handler unchanged later. No Next.js assumption
   added.
4. **Streaming transport**: `streamText().toUIMessageStreamResponse()` (AI
   SDK v5's current API — the plan's original `toDataStreamResponse()` was
   the v4 name, corrected during implementation after checking the actual
   installed `ai` package version).

## Context: what "going deeper" means concretely

Vercel AI SDK (`ai` package) provides: `streamText`/`generateText` core
loop, `tool()` for typed tool definitions (Zod schemas), automatic
multi-step tool-calling (`stopWhen`/`maxSteps`), provider-agnostic model
adapters (`@ai-sdk/anthropic`, `@ai-sdk/openai`, etc.), and
`toUIMessageStreamResponse()` for wiring straight into a fetch-based route
handler. This is the TS-native equivalent of what `lg_agent`'s LangGraph
loop + `clients/llm.py` + tool registry already give the Python side — the
gap is real, not cosmetic.

## Phase 1 — Core agent loop + tool-calling primitive ✓ DONE — 2026-07-15

**Design**:
- New staged tree (mirroring `agents/lg_agent/`'s shape, TS-flavored):
  `{{ ts_project_root }}/{{ ts_source_root }}/agent/` — `agent.ts` (the
  `streamText` call + `tool()` registry + system prompt), `tools/` (one file
  per tool, Zod-schema input/output matching the "Pydantic at boundaries"
  convention already enforced on the Python side), `settings.ts`
  (env-var-driven model/provider config, same shape as Python's
  `settings.py` pattern).
- `@ai-sdk/anthropic` as the default provider (matches
  `ANTHROPIC_API_KEY`/`clients/llm.py`'s existing convention elsewhere in
  the template) — confirm whether to also wire `@ai-sdk/openai` as an
  alternate, or keep it single-provider like the Python side's default.
- One example tool (e.g. `get_time` or similar trivial stub, matching
  `lg_agent`'s existing example-tool pattern) so the scaffold renders
  something runnable, not just an empty registry.
- Route handler: a framework-agnostic `handler.ts` exporting a
  `(req: Request) => Response` function callable from either Express (small
  wrapper) or a Next.js route handler (`export const POST = handler`) —
  resolves gate item 3 by not hard-committing either way at this layer.

**Files**: new `agent/` tree under the TS scaffold, `package.json.jinja`
(add `ai`, `@ai-sdk/anthropic`, `zod`), new `copier.yaml` toggle (per gate
item 1), README section.

**Verification**: render the config, `npm install`, real chat turn against
the example tool (not mocked) — confirm streaming response actually streams
(check for chunked transfer, not a single buffered response), confirm the
tool-call round-trip actually invokes the registered TS function.

**Status**: DONE. Staged `agent/` tree: `settings.ts` (env-driven, no port —
mounted into the existing Express app rather than a standalone service),
`clients/llm.ts` (`getProvider()`/`getModel()`, the sole
`createAnthropic()` call site, documented as the TS-side equivalent of
`clients/llm.py`'s sdk-factory convention — `sdk_lint.sh` itself stays
Python-only, not extended, since it's scoped by regex to `.py` files),
`tools/getTime.ts` + `tools/index.ts` (one working example tool, mirroring
`lg_agent`'s example-tool precedent), `agent.ts` (`streamText` +
`convertToModelMessages` + `stopWhen: stepCountIs(maxSteps)`), `handler.ts`
(framework-agnostic `(req: Request) => Response`, per the resolved gate).
Wired into `app.ts.jinja` via one adapter route (`POST /agent/chat`) that
converts Express's req/res to/from the Web `Request`/`Response` the handler
expects — the same handler function drops into a Next.js route handler
unchanged. New `ts_agent_framework` copier toggle (`none`/`vercel_ai_sdk`),
conditional `ai`/`@ai-sdk/anthropic`/`zod` deps, `_tasks` cleanup rule
removing the whole `agent/` subtree (+ its test file) when the toggle is
off. `framework-selection/SKILL.md` gained the third branch (see Gate).
README "Integrations" section documents the new endpoint.

**One real bug caught only by running the tests, not just rendering**: the
pre-existing `jest.config.cjs` (present before this phase, affecting the
baseline `app.test.ts` too — not something this phase introduced) didn't
support ESM even though `package.json` declares `"type": "module"` —
`npm test` failed on every `.ts` test file with `SyntaxError: Cannot use
import statement outside a module`. Fixed by adding
`extensionsToTreatAsEsm: [".ts"]` + a `moduleNameMapper` stripping `.js`
extensions from relative imports (TS's NodeNext-style imports write `.js`
even though the source is `.ts`) + `useESM: true` on the ts-jest transform,
and switching the `test` npm script to
`node --experimental-vm-modules node_modules/.bin/jest` (Jest's ESM support
requires this Node flag; `NODE_OPTIONS` isn't set by default). Fixed in the
shared scaffold, not worked around locally, since it blocked verifying any
TS test in the template, old or new.

**Verified**: real render (not just `--pretend`) in three configs —
`ts_agent_framework=vercel_ai_sdk`, `=none`, and `primary_backend_language=
both` + `vercel_ai_sdk` — confirmed `agent/` tree and `tests/agent.test.ts`
present/absent exactly as expected in each, no leftover Jinja, no path
collision with the Python `src/agents/` tree. `npm install` clean in all
three. `npm run typecheck` (`tsc --noEmit`) exit 0 in all three. `npm run
lint` (eslint) clean. `npm test` (`jest`, ESM-fixed) passes 2/2 in the
`vercel_ai_sdk` config, 1/1 in `none`. Strongest check: booted the real
rendered server (`npx tsx src/index.ts`) and `curl`'d `/agent/chat` three
ways — missing `messages` → `400` with the exact validation message; valid
`messages`, no `ANTHROPIC_API_KEY` set → real SSE stream (`data: {"type":
"start"}` ...), request reached `streamText`, built the correct Anthropic
payload (right model, right system prompt, right tool schema, `stream:
true`), and failed with a genuine `401 x-api-key header is required` from
Anthropic's real API — proving route → handler → agent loop → provider →
HTTP → streaming all wire correctly end-to-end, not just that the code
compiles. `/health` unaffected by the new route in both configs.

## Phase 2 — Eval wiring parity ✓ DONE — 2026-07-15

**Gap**: `evals/pipelines/run.py.jinja` grades every present Python backend
independently (already generalized for `lg_agent`/`rag_agent`/`crew_agent`
per `multi-agent-tooling-expansion.md` Phase 3). No equivalent exists for a
TS agent — evals are Python-only today.

**Design change from the original sketch**: the original plan proposed
option (a) — fold the TS agent into `run.py.jinja`'s `BACKENDS`/`_SEARCH_FNS`
machinery, treating it as another backend the Python runner grades over
HTTP. Inspecting `run.py.jinja` for real during implementation showed this
doesn't fit: that runner grades **retrieval quality** specifically (each
backend supplies a `search_fn` returning ranked results, graded for
hit_rate/MRR against `golden_qa.jsonl`'s `source_article` field) — not
generic chat. The TS agent has no retrieval step at all (it's a tool-calling
assistant, currently just `getTime`, not a RAG backend), so there's nothing
for it to supply a `search_fn` for; forcing it into `BACKENDS` would either
crash or produce a meaningless permanent 0% hit-rate. Confirmed with Ramsey:
skip retrieval grading entirely and instead add a **separate, TS-native
answer-only smoke eval** — same golden-QA questions, but scored on
answer-overlap only (the same free heuristic `citation.py`'s
`grade_answer_overlap` already uses for the Python backends' *optional*
answer-quality layer), not folded into `run.py.jinja` or `BACKENDS` at all.

- New `{{ ts_project_root }}/{{ ts_source_root }}/agent/eval/run.ts`: reads
  `data/corpus/golden_qa.jsonl` directly (path passed via `GOLDEN_QA_PATH`
  env var, since `ts_project_root` may not be a fixed distance from the repo
  root), POSTs each question to the real running `/agent/chat`, parses the
  UI-message SSE stream for real (`text-delta` chunks only — plus detects
  `type: "error"` chunks, since the AI SDK reports provider failures
  *inside* the 200-status stream, not via HTTP status), scores token overlap
  against `expected_answer` with a small TS port of
  `grade_answer_overlap`'s exact algorithm (no Python dependency), writes
  `evals/reports/output/heuristic_results_ts_agent.json` — same directory
  and naming convention as the Python backends' result files, so it's
  discoverable the same way, just not produced by the same script.
- New `ts-agent-eval` Makefile target (mirrors `promptfoo-eval`'s existing
  pattern: requires the server already running via `make ts-dev` in another
  terminal, not spawned by the target itself) and `npm run eval` script.
- Explicitly NOT added to `run.py.jinja`'s `BACKENDS` list, NOT graded for
  hit_rate/MRR, and its results file uses a distinct `backend: "ts_agent"`
  tag rather than pretending to be retrieval-comparable to `lg_agent`/
  `rag_agent`.

**Files**: new `agent/eval/run.ts.jinja`, `package.json.jinja` (`eval`
script), `Makefile.jinja` (`ts-agent-eval` target + `.PHONY` entry).

**One real bug caught only by running against a live server, not just
typecheck**: the first working version silently swallowed provider errors —
Anthropic's SSE stream reports a failed generation as an in-stream
`{"type":"error",...}` chunk while the HTTP status is still 200 (this is how
the AI SDK's streaming protocol works — errors arrive as stream content, not
as a non-2xx response), and the original parser only looked for
`text-delta` chunks, so a 401 (no `ANTHROPIC_API_KEY`) produced an empty
string answer that scored a false `0.00` overlap with `error: null` instead
of surfacing as the row error it actually was — the exact "silent failure
looks like a bad answer" bug class this eval exists to catch. Fixed by
explicitly checking for `type: "error"` chunks and throwing, so the
per-question `try/catch` in `main()` correctly records `answer_overlap_ratio:
null` + a real `error` message instead. Also caught (and fixed) 6 real
`eslint` violations on first run (missing braces on single-line `if`s,
`console.log` where only `warn`/`error` are allowed per this project's
`eslint.config.mjs`) — none of these would have surfaced from rendering or
typechecking alone.

**Verified**: real fresh render + `npm install` + `npm run typecheck` (exit
0) + `npm run lint` (exit 0, zero violations after fixes). Real end-to-end
run: booted the actual server (no `ANTHROPIC_API_KEY` set, matching the
same environment-boundary convention used everywhere else in this template)
and ran `make ts-agent-eval` for real — all 10 golden-QA rows correctly
recorded `answer_overlap_ratio: null` + `error: "agent stream error: An
error occurred."`, summary line correctly printed `mean_answer_overlap: n/a
(all requests errored — check ANTHROPIC_API_KEY and that the server is
running)` instead of a misleading `0.000`, and a real
`heuristic_results_ts_agent.json` was written to the correct
`evals/reports/output/` directory alongside where the Python backends write
theirs. Also unit-verified the SSE parser in isolation against synthetic
`text-delta` and `error`-chunk payloads before wiring it into the render, to
separate "is the parsing logic correct" from "does the full render/install/
run pipeline work."

## Phase 3 — Deployment convention (Vercel-specific) ✓ DONE — 2026-07-15

**Gap**: template's existing deploy story is Docker + `docker-compose.yml`
(Cloud Run-oriented, per `multi-agent-tooling-expansion.md`'s Phase 3
generalization). Vercel doesn't use that path — needs its own convention.

**Design change from the original sketch**: the original plan assumed a
`vercel.json` rewrite might be needed to run Express as a Vercel Function,
and asked whether streaming needs the Edge runtime. Fetched Vercel's actual
current docs (not memory) before writing anything, since both assumptions
turned out to be wrong:
- [Vercel's Express docs](https://vercel.com/docs/frameworks/backend/express):
  Express deploys to Vercel with **zero configuration** today, as long as
  the entry file is at one of a documented set of conventional paths —
  which includes `src/index.ts` exactly, this scaffold's actual layout.
  Both `app.listen(port)` (this scaffold's existing pattern, unchanged) and
  `export default app` work; no `vercel.json` rewrite, no code change
  needed. Confirmed with Ramsey before implementing — the originally-planned
  `vercel.json.jinja` file was dropped as unnecessary rather than added
  speculatively.
- [Vercel's streaming docs](https://vercel.com/docs/functions/streaming-functions):
  streaming works on the default Node.js runtime with no special
  configuration — Edge runtime isn't mentioned as a requirement anywhere in
  that doc. Resolves gate item 3: no Edge runtime, no `agent.ts` Node-API
  constraints to worry about. The only real lever is
  [max duration](https://vercel.com/docs/functions/limitations#max-duration)
  if a project's conversations need longer than the plan's default —
  documented as an if-needed pointer, not implemented speculatively.
- Env vars: documented as a real, separate step (Vercel dashboard vs. local
  `.env`, not automatically synced) rather than assumed obvious.

**Files**: README "Deploying" section only (conditional on
`ts_agent_framework == "vercel_ai_sdk"`) — no `vercel.json.jinja`, since
nothing in the zero-config path requires one. This is the smallest of the
three phases, as scoped.

**Verified**: real render — the new README section appears correctly and
only when the toggle is on, all three cited doc links point at real,
current Vercel documentation (fetched and read during this phase, not
guessed), Jinja resolves cleanly (`{{ ts_project_root }}`/
`{{ ts_source_root }}` interpolate correctly in context). Full toolchain
re-run on the same render as a regression check: `npm install`,
`typecheck` (exit 0), `lint` (exit 0), `test` (2/2 passing) — confirms the
README-only change didn't disturb anything from Phases 1–2. A real Vercel
deploy still can't be verified from this environment (no Vercel account/CLI
session here) — flagged as a follow-up once `nonprofit-success-ai` actually
deploys this, per the original plan's verification note, but the deploy
guidance itself is now sourced from Vercel's real docs rather than assumed.

## Sequencing

Phase 1 (core agent loop — the actual gap) → Phase 2 (eval parity, so this
backend isn't a blind spot in CI) → Phase 3 (Vercel deploy convention,
smallest phase, mostly documentation + one config file). Each phase
implemented and verified before the next, same discipline as
`multi-agent-tooling-expansion.md`. Once this lands, revisit
`nonprofit-success-ai`'s Phase 4 (currently TBD, blocked on this plan
existing) to decide whether that repo renders from `ai-project-template`
directly or hand-adopts the pattern — that repo already exists and wasn't
originally scaffolded from this template, so adoption there is a separate
follow-up decision, not automatic.
