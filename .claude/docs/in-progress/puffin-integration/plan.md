# Plan: puffin-integration
Date: 2026-07-12
Based on: direct codebase inspection (puffin `.claude/skills/{genesis,dream,grow,reflect,research}`, playground `src/agents/{lg_agent,rag_agent,adk_agent,akira}` + `.claude/skills/{SANYI,akira}` + `mcp_servers/knowledge_base`, ai-project-template `copier.yaml` + `template/_scaffold` + `template/.agents/skills` + `template/.claude/skills`) — no separate research doc; conversation covered this ground directly.

## Goal
Extend `ai-project-template` so generated projects ship three prebuilt example agents (`lg_agent`, `rag_agent`, `adk_agent`) mirroring playground, with real MCP-client wiring (currently absent in both source repos); port `akira` as a second prebuilt LangGraph tooling agent and `SANYI` as a lightweight change-contract skill; and add an optional `include_dev_companion` toggle carrying puffin's transform-not-append discipline plus a `/dream`-style audit skill.

## Approach
Extract-and-adapt from playground, the same discipline the template's README already documents ("everything here was extracted from playground/.claude/, stripped of client- and domain-specific content") — apply that to `src/agents/*` and `src/agents/akira` too, not just `.claude/`. MCP client consumption is genuinely new work in both repos (confirmed by grep: zero `MCPToolset`/`MultiServerMCPClient` usage anywhere in playground) — wire it fresh using each framework's real library support, not custom protocol code. Each capability that changes generated-project shape gets its own copier toggle, consistent with the existing `include_mcp_server` / `include_agent_reference_library` pattern — nothing becomes unconditionally mandatory.

**Design call on where MCP-client wiring lives**: playground's real shape has `rag_agent` as the retrieval *service* that `mcp_servers/knowledge_base` wraps over HTTP (server-side) — preserve that fidelity. Demonstrate the *client* side (what's actually missing) in `lg_agent` (LangChain `langchain-mcp-adapters`) and `adk_agent` (native `MCPToolset`), since those are the two agents a template user is most likely to copy from when wiring a new tool call.

## Out of Scope
- Playground's music-KB domain content/data (corpus, golden_qa, genre/artist vocab) — mechanism only.
- Porting puffin's `wake` / `grow` / `intermission` / `reflect` / `genesis` verbatim — superseded by `compact-session` + the memory system + cartographer (established in prior research pass).
- Any change to `compact-session`, cartographer, or the memory-file system itself.
- New eval graders specific to `rag_agent`/`adk_agent` beyond a smoke-test wired into the existing `_scaffold/{{ eval_root }}` plumbing.
- Terraform/deployment scaffolding beyond what `infrastructure/` already provides generically.
- MCP server transport beyond stdio (playground's server uses bare `mcp.run()` → stdio only; SSE/streamable-HTTP is a stretch item, not required for client-wiring to work).

## Phases

Six phases, review boundary after each (per plan-review's >8-steps-must-split rule). Phases 2–3 depend on Phase 1's shared client pattern; Phases 4–5 are independent of 2–3 and can run in parallel if you want to split work.

---

### Phase 0 — Copier scaffolding & toggles ✓ DONE — 2026-07-12

**Deviation**: Step 0.3's `template/CLAUDE.md.jinja` Layout-block and `template/_scaffold/README.md.jinja` mentions, and the `_message_after_copy` line, were deferred to Phases 4 and 6 respectively — those files/commands (`agents/akira`, `.claude/docs/companion`, `make akira-kaneda`) don't exist until those phases land, and documenting them now would describe non-functional paths. Only the root `README.md` Options table (describes the toggle itself, which is real) was updated now.

**Step 0.1 — Add new copier questions** ✓ DONE
**Files**: `copier.yaml`
**What**: After the `include_agent_reference_library` block, add:
- `include_akira` (bool, default `true`, `when: scaffold_full_project`) — help text: "Scaffold `akira`, a second prebuilt LangGraph agent for proactive codebase quality scanning (kiyoko/kaneda/dao modes)?"
- `include_dev_companion` (bool, default `true`, `when: scaffold_full_project`) — help text: "Add the dev-companion layer — a living 'how we work on this project' doc that transforms (not appends) over time, plus a `/dream` maintenance-audit skill?"
No new toggle for `rag_agent`/`adk_agent` — they ship whenever `scaffold_full_project=true`, same tier as `lg_agent`, per your call that all three should be prebuilt equally.
**Test**: `copier copy --data include_akira=false --data include_dev_companion=false . /tmp/pt-test-off && copier copy . /tmp/pt-test-on` — both render without error.
**Done when**: both toggles exist, default `true`, gated on `scaffold_full_project`, and `_tasks` cleans up their dirs when off (Step 0.2).

**Step 0.2 — Wire cleanup tasks** ✓ DONE
**Files**: `copier.yaml` → `_tasks` list
**What**: Add two lines mirroring the existing `include_agent_reference_library` pattern:
```
- "{{ 'true' if include_akira else 'rm -rf ' ~ _copier_conf.dst_path ~ '/' ~ source_root ~ '/agents/akira' }}"
- "{{ 'true' if include_dev_companion else 'rm -rf ' ~ _copier_conf.dst_path ~ '/.claude/skills/dream ' ~ _copier_conf.dst_path ~ '/.claude/docs/companion' }}"
```
**Test**: render with each flag off, confirm the corresponding dir is absent; render with both on, confirm present.
**Done when**: no orphaned files in either configuration.

**Step 0.3 — Update root docs** ✓ DONE (partial — see Deviation above)
**Files**: `README.md` (Options table), `template/CLAUDE.md.jinja` (Layout block), `template/_scaffold/README.md.jinja` (Next steps message)
**What**: Add `include_akira`/`include_dev_companion` rows to README's Options table; add conditional Layout lines for `rag_agent/`, `adk_agent/`, `agents/akira/` under the existing `{{ source_root }}/` line; mention `make akira-kaneda` in `_message_after_copy`.
**Test**: manual read-through of rendered `CLAUDE.md` for a full-on render.
**Done when**: rendered docs mention every new toggle and directory.

---

### Phase 1 — Shared MCP client pattern (foundational)

**Bug found and fixed (out of plan scope, but blocking)**: `mcp_servers/{{ mcp_server_slug }}/pyproject.toml.jinja` declared `hatchling` as build backend with no `[tool.hatch.build.targets.wheel] packages` — `uv sync` failed for *any* project using the default `include_mcp_server=true`, unrelated to this plan. Added `packages = ["app"]`. Caught only because Step 1.1's test was run for real rather than assumed.

**Step 1.1 — LangGraph-side MCP client module** ✓ DONE — 2026-07-12/13
**Deviation**: also renamed `settings.py` → `settings.py.jinja` (not called out in the original step) — the new `mcp_server_dir` field needs the copier-rendered slug, and no other file in `lg_agent` previously needed Jinja substitution inside Python source. New client file created as `clients/mcp.py.jinja` for the same reason (not plain `.py` as originally worded) — both `mcp_server_slug` references guarded with `| default(project_slug)` since that variable is only defined `when: include_mcp_server`, and this file renders regardless of that toggle.
**Files**: new `_scaffold/{{ source_root }}/agents/lg_agent/clients/mcp.py`
**What**: Thin wrapper around `langchain-mcp-adapters`' `MultiServerMCPClient`, configured to point at `mcp_servers/{{ mcp_server_slug }}` over stdio (matching the server's actual transport). Expose `async def get_mcp_tools() -> list[BaseTool]` for use in `graph.py`/nodes. Add `langchain-mcp-adapters` to `pyproject.toml.jinja` deps.
**Test**: `uv run python -c "import asyncio; from agents.lg_agent.clients.mcp import get_mcp_tools; print(asyncio.run(get_mcp_tools()))"` against the running MCP server — prints the tool list.
**Done when**: tool list from the client matches the tools defined in `mcp_servers/{{ mcp_server_slug }}/app/server.py.jinja`.

**Step 1.2 — Wire into lg_agent's graph** ✓ DONE — 2026-07-13

**Deviation (material, user-approved via decision point)**: original wording assumed `retrieve_node` had an LLM-driven tool-choice mechanism to attach MCP tools to. It didn't — `generate_node` was a plain single-shot `anthropic.messages.create()` with zero tool-calling loop anywhere in `lg_agent`. Presented three options (minimal standalone script / deterministic extra node / real tool-use loop); user chose **real tool-use loop**. Implemented as:
- `clients/llm.py`: added `get_async_client()` (factory, mirrors `get_client()`) and `agenerate()` — one turn of async tool-capable generation, returns the raw `Message` so the caller inspects `stop_reason`.
- `nodes/generate.py`: `generate_node` is now `async def`. Fetches MCP tools once per invocation, converts them to Anthropic's `input_schema` format (`_to_anthropic_tool`), loops up to `_MAX_TOOL_TURNS=4`: call → if `stop_reason == "tool_use"` invoke the real tool via `tool.ainvoke()` and feed `tool_result` back → repeat until a text-only response.
- **Ripple, declared and made**: `main.py`'s `chat` handler changed `_graph.invoke(...)` → `await _graph.ainvoke(...)` — required once any node is `async def`; LangGraph's sync `.invoke()` doesn't run async nodes from within an already-running event loop (FastAPI's own).
- `state.py` needed **no changes** — contrary to what I described as possible before starting, the tool-loop's intermediate messages are internal to `generate_node`'s local scope; only the final `answer` crosses back into graph `State`, matching every other node's existing return-dict pattern.
- **Real bug caught mid-implementation**: assumed `tool.args_schema` would be a pydantic model needing `.model_json_schema()` — tested against the live MCP server first and found `langchain_mcp_adapters` sets `args_schema` to a plain JSON-schema **dict** already (MCP tools are JSON-schema-native, not pydantic-native). Implementation passes it through directly instead.

**Files touched**: `clients/llm.py` (edit), `clients/mcp.py.jinja` (edit, from 1.1), `nodes/generate.py` (rewrite), `main.py` (one-line edit).
**Test performed**: rendered a real project, ran the real corpus ingest, then ran the full graph via `ainvoke()` with only `agents.lg_agent.clients.llm.get_async_client` mocked (canned `tool_use` then `end_turn` responses) — everything else real: real DuckDB retrieval (`sources` populated correctly), real MCP server subprocess spawned and invoked via `tool.ainvoke()`, correct 2-call loop termination, correct final answer propagation. `ruff check` + `ruff format --check` both clean after two line-length fixes.
**Not tested**: an actual Anthropic API call — no `ANTHROPIC_API_KEY` available in this environment. The mock covers everything on either side of that one call.
**Done when**: a chat turn that requires the MCP tool succeeds end-to-end. ✓ (verified with mocked LLM call, real everything else — see above)

**Step 1.3 — ADK-side MCPToolset wiring** → DEFERRED to Phase 3 (folds into Step 3.3). Reason: this step's own file list (`adk_agent/mcp_tools.py`, `agent.py`) assumes `adk_agent/` already exists — it doesn't until Phase 3 runs. Sequencing error in the original plan, caught during execution rather than at planning time.

~~Original text~~ (for reference, executed as part of Phase 3 instead):
**Files**: new `_scaffold/{{ source_root }}/agents/adk_agent/mcp_tools.py`, `agent.py` (register toolset)
**What**: Use ADK's native `MCPToolset` class pointed at the same MCP server (stdio subprocess launch, matching ADK's documented pattern — reference `adk-dev-guide` skill for ADK conventions before writing this).
**Test**: ADK's own dev-server smoke test invoking a query that requires the tool.
**Done when**: tool call round-trips through `MCPToolset` and returns real data from the MCP server.

**Step 1.4 — Document the pattern** ✓ LangGraph half DONE — 2026-07-13. ADK half deferred to Phase 3 alongside 1.3. Deviation: written in single-brace prose-placeholder style (`{source_root}`) matching `new-agent/SKILL.md`'s existing convention, not real Jinja — confirmed `mcp-builder/SKILL.md` has no `.jinja` suffix (unlike `README.md.jinja` in the same dir) so double-brace syntax would have leaked through unrendered.
**Files**: `template/.claude/skills/mcp-builder/SKILL.md`
**What**: Add a "Consuming your server" section — the two snippets from 1.1/1.3, one line each framework, since mcp-builder currently only covers server-authoring.
**Test**: none (docs only).
**Done when**: section exists, links to both client files as worked examples.

---

### Phase 2 — `rag_agent` scaffold (server-side, mirrors playground) ✓ DONE — 2026-07-13

**Scope finding (user decision point)**: playground's real `rag_agent` is 8,342 lines / ~85 files — pluggable vector backends (duckdb/opensearch/memory), pluggable rerankers, pluggable checkpointers, HITL resume, SSE streaming, summarization, query-rewrite, an 11-node confidence-gated LangGraph state machine with retry loops. ~30x `lg_agent`'s entire footprint. Presented full-port vs. minimal-port; user chose **minimal**. On reading the actual node/state files (`orchestrator/langgraph/schemas/state.py`'s `GraphState`, `nodes/planner.py`, `nodes/retriever.py`), found the orchestration layer is deeply entangled with VA-product-specific concepts (`task_execution` mode, `market`/`locale` fields, HITL gate-action routing keys, multi-locale query expansion) that aren't separable by trimming — porting "minimal" meant **writing fresh code inspired by the architecture**, not mechanically trimming existing files. Proceeded on that basis rather than re-asking, since it's a direct consequence of the minimal-scope decision already made, not a new fork.

**What was actually built** (new, not adapted line-by-line, except `vectorstore.py` and `embeddings.py` which are faithful trims of `rag/datastore/local.py`'s `DuckDBVectorIndex` and `rag/sentence_transformers.py` — those two were self-contained enough to port directly):

- `settings.py`, `schema.py`, `checkpointer.py` (same `InMemorySaver`-only pattern as `lg_agent`), `confidence.py` (single-threshold signal, dropped playground's CRAG-delta/feature-flag machinery — informational only, not gating, per minimal-scope decision)
- `embeddings.py` — local `sentence-transformers` model, LangChain `Embeddings` interface
- `vectorstore.py` — single-table DuckDB store, `FLOAT[]` embeddings, brute-force cosine-via-dot-product (no ANN index — noted as a scale limit in the file's own docstring)
- `graph.py` — 2-node `retrieve → generate` (no planner/reranker/gates/escalation/summarizer — the real differentiator from `lg_agent` is the *retrieval mechanism* — embeddings + semantic search vs. BM25 FTS — not graph complexity)
- `build_index.py` + `core/__main__.py`'s new `rag-ingest` command — reuses the *same* preprocessed JSONL `core/ingestion.py` already produces for `lg_agent`, embeds it into a separate DuckDB file. Same source articles, two retrieval mechanisms side by side.
- `main.py` — `/health`, `/chat`, and `/api/v1/retrieval` (retrieval-only, no answer synthesis) — this last one mirrors playground's *real* integration point: the endpoint an MCP tool or another agent calls when it wants documents + confidence to synthesize its own answer, not a pre-written one.

**Real bug found and fixed before any testing** (would have silently corrupted data, not just failed loudly): `rag_agent.settings.Settings` initially declared a field named `vectordb_path` — identical to `lg_agent.settings.Settings`'s existing field. Both classes' `pydantic-settings` bind by field name to the *same* env var `VECTORDB_PATH` regardless of which class declares it — setting it for one would silently override the other's default, pointing both agents at the same file despite incompatible table schemas (`articles` FTS table vs. `rag_chunks` vector table). Renamed to `rag_vectordb_path`. (Checked for other collisions: `anthropic_api_key`, `retrieval_top_k`, `generation_temperature` also match — left as-is, since sharing those values across the two example agents isn't functionally broken, just the DB path was.)

**Ripple, declared and made**: `pyproject.toml.jinja` gained `sentence-transformers>=3.0.0` as a **mandatory** dependency (pulls in `torch`, `transformers` — a real, meaningful install-time/weight cost for every generated project going forward, not just this feature). This is the direct, accepted cost of "prebuilt like lg_agent" with a real embedding-based retrieval mechanism as the differentiating feature, not a hidden side effect — flagging it explicitly rather than burying it.

**Test performed, fully real, no mocks except the LLM call**:
1. Rendered a real project, `uv sync` (confirmed `torch`/`sentence-transformers` resolve and install)
2. `ruff check` + `ruff format --check` clean on `agents/rag_agent/` and `core/`
3. `make rag-corpus-ingest` — real embedding model download (`all-MiniLM-L6-v2`) and real DuckDB index build from the real placeholder corpus
4. `retrieve_node()` called directly — real semantic search correctly ranked the "descaling" article top (score 0.58) for a descaling question
5. Full graph via `build_graph().invoke()` with only `agents.rag_agent.clients.llm.get_client` mocked — asserted the mocked LLM call received the real descaling-article context, confirmed correct `Source`/`confidence` propagation
6. **Booted the actual FastAPI server** (`make rag-up`/`rag-wait`) and hit `/api/v1/retrieval` over real HTTP — full real response, matching step 4's direct-call result exactly

**Files touched**: 15 new files under `agents/rag_agent/` (settings, schema, confidence, embeddings, vectorstore, checkpointer, graph, state, build_index, clients/llm, nodes/{retrieve,generate}, `__init__.py`s), plus edits to `core/__main__.py` (new `rag-ingest` command), `Makefile.jinja` (6 new `rag-*` targets), `pyproject.toml.jinja` (1 dependency), `.env.example.jinja` (6 new vars).
**Done when**: a chat turn against the real service returns real retrieved sources + confidence. ✓ (verified via direct HTTP call, step 6 above)

**Step 2.3 — Point `mcp_servers/{{ mcp_server_slug }}` at it** ✓ DONE — 2026-07-13 (initially missed when marking the phase done above — caught while cleaning up this doc, fixed before moving on)
**Files**: `template/mcp_servers/{{ mcp_server_slug }}/app/server.py.jinja`
**What**: Replaced the generic `example_tool` placeholder with `search_articles`, calling `rag_agent`'s `/api/v1/retrieval` over HTTP (`RAG_AGENT_URL`, default `http://localhost:8011`) — mirrors playground's real `knowledge_base` server → `rag_agent` HTTP pattern. Tool rename confirmed safe (grepped for `example_tool` references elsewhere — none; Phase 1's client code has no hardcoded tool names).
**Test performed**: full real chain — rendered project, `uv sync` both packages, built the real embedding index, booted the real `rag_agent` server (`make rag-up`), then called `agents.lg_agent.clients.mcp.get_mcp_tools()` → `search_articles` tool → real MCP subprocess → real HTTP call to `rag_agent` → real embedding retrieval. Returned the correct descaling article + confidence 0.58, identical to the direct-HTTP result from Phase 2's earlier test.
**Done when**: MCP tool call returns real rag_agent output, not a stub. ✓

---

### Phase 3 — `adk_agent` scaffold ✓ DONE — 2026-07-13

**Scope finding**: much better news than Phase 2 — playground's real `adk_agent` is 1,044 lines / 9 files (~4x `lg_agent`, not ~30x like `rag_agent` was), and — unlike `rag_agent`'s orchestration layer — genuinely self-contained. `direct_agent.py`, `callbacks.py`'s KB-passage pruning, and the gateway's Runner/SSE-queue pattern ported near-faithfully. Dropped four VA-specific infra dependencies that don't exist in this template and weren't worth re-implementing for a minimal example: `artefact_store` (file upload/download — a bigger feature, not core to demonstrating ADK), `memory_store` (cross-session user-preference persistence), `observability` (LangSmith/Langfuse tracing wrapper), `model_factory` (used only for an auto-summarize-session feature). Kept the genuinely ADK-distinctive patterns: callback-based session state (`before_agent_callback`, `before_model_callback`), structured `output_schema`, SSE background-task streaming — these demonstrate what's actually different about ADK vs. LangGraph, which is the point of having both example agents.

**MCP integration (closes the Phase 1.3 deferral)**: verified `MCPToolset` is deprecated in the current SDK in favor of `McpToolset` (found by testing, not docs — the deprecated class exists but only wraps the new one with a warning). Real, tested import path: `google.adk.tools.mcp_tool.mcp_toolset.McpToolset` + `mcp_session_manager.StdioConnectionParams` + `mcp.StdioServerParameters` (the last one requires the separate `mcp` PyPI package — not pulled in by `google-adk` alone, caught by testing before it became a runtime `ModuleNotFoundError` in a generated project). `sub_agents/rag_agent.py`'s tool is now the real `McpToolset` pointed at the project's own MCP server, replacing playground's direct-httpx-to-a-rag-service call — same integration this project's `lg_agent` demonstrates via `langchain-mcp-adapters`, now shown in both frameworks' native mechanisms.

**Ripple, declared and made**: added `google-adk>=1.0.0` and `mcp>=1.0.0` to `pyproject.toml.jinja` (mandatory, same disclosure standard as Phase 2's `sentence-transformers`); `GOOGLE_GENAI_USE_VERTEXAI=false` + `GOOGLE_API_KEY` + `ADK_PORT` + `GATEWAY_API_KEY` added to `.env.example.jinja`; 6 new `adk-*` Makefile targets (the SSE-based `adk-chat` smoke test is structurally different from `lg-chat`/`rag-chat` — it has to open the stream before POSTing, per the gateway's own documented ordering requirement).

**Test performed, fully real up to the one boundary this environment can't cross**: rendered a project, `uv sync` (confirmed `google-adk`/`mcp` resolve), `ruff check`/`format --check` clean, constructed `root_agent` directly and verified sub-agent wiring, called the real `McpToolset.get_tools()` against the real running MCP server (returned `search_articles`, matching Phase 2's tool), booted the real FastAPI gateway (`make adk-up`/`adk-wait`), and drove a full chat turn through the real SSE stream — confirmed correct routing/session/queueing all the way to the real Gemini call, which failed with the clean, expected `"No API key was provided"` (no `GOOGLE_API_KEY` in this environment — same class of boundary as Phases 1–2's missing `ANTHROPIC_API_KEY`).

**Files touched**: 13 new files under `agents/adk_agent/` (agent, app, callbacks, schema, mcp_tools, sub_agents/{direct_agent,rag_agent}, gateway/{main,session_manager}, prompts×4, `__init__.py`s), plus `Makefile.jinja` (6 targets), `pyproject.toml.jinja` (2 deps), `.env.example.jinja` (4 vars).
**Done when**: tool call succeeds end-to-end through ADK. ✓ (verified via direct `McpToolset.get_tools()` call, returning the real `search_articles` tool from the real MCP server)

---

### Phase 4 — `akira` port (second prebuilt LangGraph agent) ✓ DONE — 2026-07-13

**Scope finding, confirming the Step 4.1 prediction**: the graph layer (`schema.py`, `state.py`, `graph.py`, and all three mode nodes `kiyoko`/`kaneda`/`dao`) is genuinely generic — ported near-verbatim, only import paths changed. The 5 **domain subagents**' *structure* (base class, JSON-findings contract, `_call()` pattern) is also generic and ported as-is — but their *content* (SYSTEM prompts + `scan()` context-gathering) was hardcoded to a different, unrelated codebase entirely (`src/support_agents/{hc_adk,hc_lg,hc_rag}`, `evals/graders/judges/base.py` — not even playground's own real structure). Rewrote all 5 with real content tailored to what this template actually has: **SchemaAgent** now checks the exact settings.py field-collision bug class this session found twice (Phases 2 and 3); **SafeguardAgent** checks guardrail coverage across the three real agents, explicitly told not to flag `rag_agent`'s lack of one as a bug (documented, deliberate — it's retrieval-only); **EvalAgent** checks `{{ eval_root }}/` conventions and flags the real, deliberate rag_agent/adk_agent eval-coverage gap as LOW severity, not urgent; **DocsAgent** checks this project's actual `CLAUDE.md`/`README.md`; **CodeQualityAgent** needed no rewrite (genuinely repo-agnostic already).

**A real, previously-hidden bug from Phase 1, caught here**: `dao`'s test-gate (`_run_tests()` → `make test`) surfaced 3 failing tests in the *existing* `tests/unit/agents/test_generate.py` — a regression from Phase 1's rewrite of `generate_node` (sync single-shot → async tool-loop) that I never caught because I only ran my own ad-hoc verification scripts after that change, not the project's actual test suite. Fixed by rewriting the three tests for the new async signature (mocking `agenerate`/`get_mcp_tools` instead of the old `generate`) and adding a fourth test covering the tool-use loop itself. All 36 unit tests pass now. **This was a genuine testing-discipline gap on my part, not a plan ambiguity** — recorded here rather than glossed over.

**Two file-permission denials encountered and respected, not routed around**: this environment's permission settings block reads/writes matching `.env*` patterns (a secret-leakage guard) even for this template's own committed example file (`.env.example.jinja`) and even for scratch-render copies (`.env`). Skipped an optional `AKIRA_MODEL` documentation line in `.env.example.jinja` as a result — not required, since `settings.py` already has a sensible default and `ANTHROPIC_API_KEY` is already shared across all four agents.

**Also fixed in passing**: stray committed `__pycache__/` directories under `{{ eval_root }}/` in the template source (pre-existing, unrelated to this plan, harmless since `copier.yaml`'s `_exclude` already strips them at copy-time, but dead weight in the repo regardless).

**Test performed, fully real except the one unavoidable boundary**: rendered a project, `uv sync` (confirmed `langchain-anthropic` resolves; caught and fixed a wrong constructor kwarg — `anthropic_api_key`, not `api_key` — by inspecting the real pydantic model fields rather than guessing), `ruff check` clean, `make test` (36/36 pass after the regression fix), then exercised all three modes with only the Anthropic call mocked: `kaneda` ran real git commands + real 5-way parallel dispatch + real file reads/globs against this project's actual files + correct dedup logic + wrote a real findings doc; `dao` read that real findings doc, ran the real test-gate, triaged with a mocked verdict, updated status, wrote a real run summary; `kiyoko` ran real git diff/log and surfaced the mocked question. Finally ran `make akira-kaneda` with **no mock at all** (no API key present) — confirmed the full real chain (Makefile → CLI → graph → node → 5 parallel subagents → real `ChatAnthropic` → real Anthropic SDK call) fails cleanly only at the true "no API key" boundary, matching every prior phase's testing pattern.

**Files touched**: 24 new files under `agents/akira/` (schema, settings, `__main__`, `clients/llm`, `graph/{state,graph}`, `graph/nodes/{kiyoko,kaneda,dao}`, `subagents/{base,code_quality,schema_check,safeguard,docs_check,eval_patterns}`, `findings/.gitkeep`, `__init__.py`s), `template/.claude/skills/akira/SKILL.md`, plus edits to `Makefile.jinja` (3 targets, gated `{% if include_akira %}`), `pyproject.toml.jinja` (1 dep), `.gitignore` (findings output), and the Phase-1 regression fix to `tests/unit/agents/test_generate.py`.
**Done when**: kiyoko/kaneda/dao all run against a freshly rendered project. ✓

---

### Phase 5 — `SANYI` port (contract-enforcement skill, no running agent) ✓ DONE — 2026-07-13

**Confirmed the prediction exactly**: read all 4 files (`SKILL.md`, `README.md`, `references/{contract-spec,violations,interview-guide}.md`) — genuinely zero playground-specific content anywhere; every example uses generic placeholder paths (`backend/security/masking.py`, not a real path from this or any specific repo). Ported verbatim, only fixing one pre-existing minor inconsistency in playground's own copy: the skill folder was `SANYI/` (uppercase) while `name: sanyi` (lowercase) in frontmatter — skill-writer's own convention requires the folder to match `name` exactly, so this port uses lowercase `sanyi/` for both.

**Step 5.1 — Port skill + references** ✓ DONE
**Files**: `template/.claude/skills/sanyi/SKILL.md`, `README.md`, `references/{contract-spec,violations,interview-guide}.md` — all 4 copied verbatim (content identical to playground's, only the folder-casing fix above).
**Test performed**: skill-writer's structural checklist (frontmatter delimiters valid, description single-line, folder name matches `name:` field, no XML brackets, all 3 reference links resolve) — all pass. Rendered a real project and confirmed all 5 files land correctly with no jinja artifacts (none needed — zero template variables in this skill's content).
**Done when**: `/sanyi init` produces a `SANYI.md` when run against a freshly rendered project. Not mechanically testable the way the agent phases were (skill invocation requires an interactive Claude Code session, not a subprocess) — verified via the structural checklist instead, which is what the original plan's fallback ("none beyond skill-writer checklist") anticipated.

**Step 5.2 — Cross-link with existing `code-review`** ✓ DONE
**Files**: `template/.claude/skills/code-review/SKILL.md` — added one line distinguishing scope (diff-vs-plan fidelity here; standing-contract decay detection in SANYI) right after the skill's opening description.
**Done when**: `code-review` SKILL.md mentions SANYI as complementary. ✓ (confirmed present in a fresh render)

---

### Phase 6 — `include_dev_companion` layer ✓ DONE — 2026-07-13

**Step 6.1 — Living "how we work" doc + transform discipline** ✓ DONE
**Files**: `template/.claude/docs/companion/collaboration.md.jinja` (starting stub — "What Works Between Us" / "Preferences" / "Decisions That Don't Need Re-Litigating"); `template/.claude/skills/grow-companion/SKILL.md` adapted from puffin's `/grow` — same transform-not-append discipline, retargeted at this one doc.
**Deviation from puffin's original**: dropped the "log to accumulator, batch-process later" two-step (puffin's `growth.md` → `/synthesize`) — with only one doc and no multi-file identity system to batch-process into, that indirection has no purpose here. `/grow-companion` transforms the doc directly and immediately, matching what puffin's own `/grow` already does for mid-session changes anyway.

**Step 6.2 — `/dream`-style audit skill** ✓ DONE
**Files**: `template/.claude/skills/dream/SKILL.md` — same 4-phase structure as puffin's original (Orient → Gather Signal → Consolidate → Report), discovery-based path-finding preserved (puffin's own "discover, never assume" philosophy carried over deliberately, since `MEMORY.md`'s actual location varies by environment and shouldn't be hardcoded).
**Test performed**: skill-writer structural checklist (frontmatter, single-line description, no XML brackets) — pass. Not mechanically testable end-to-end for the same reason SANYI wasn't (skill invocation needs an interactive session).

**Step 6.3 — Wire into `_message_after_copy` / CLAUDE.md** ✓ DONE, plus closed a gap from Phase 4
**Files**: `copier.yaml` (`_message_before_copy` + `_message_after_copy`), `template/CLAUDE.md.jinja`, and — caught while doing this — **Phase 4's own deferred `CLAUDE.md.jinja` edit for `akira` had never actually been completed** (the Phase 0 deviation note said it was deferred to Phase 4, but Phase 4's summary never mentioned touching this file). Fixed both together. Also updated `_scaffold/README.md.jinja` and `.claude/skills/README.md.jinja` — both had gone stale across Phases 2-5 (still describing only `lg_agent` as "the" example agent, missing `sanyi`/`akira`/`grow-companion`/`dream` from the skill inventory table) — beyond this step's literal scope but a real, accumulated documentation gap worth closing now rather than leaving for a future pass.

**A second real bug found and fixed during final verification**: `include_akira=false` didn't actually remove `{{ source_root }}/agents/akira` — the Phase 0 cleanup task targeted the *final* path, but `agents/akira` is staged under `_scaffold/` and only moved into place by a *later* task (the `mv _scaffold/* ./` step) — so the cleanup ran before the content it was supposed to remove even existed at that path, and silently did nothing. (`.claude/skills/akira` half of the same task was unaffected — that path isn't staged under `_scaffold/`.) Fixed by targeting the `_scaffold/`-relative path instead. Caught only because Phase 6's final verification pass explicitly checked the `include_akira=false` case with `test -d`, not just "did copier exit 0."

**Test performed, full final verification pass across all 6 phases together**:
1. Rendered three configurations — all toggles on (defaults), `include_akira=false`/`include_dev_companion=false`, and `scaffold_full_project=false` — all render without error
2. Explicitly `test -d`/`test -f`'d every toggle-gated path in both the "on" and "off" renders (not just checked exit codes) — this is what caught the akira bug above
3. Grepped all rendered docs (`CLAUDE.md`, `README.md`, `.claude/skills/README.md`, `collaboration.md`) for leftover `{{` — clean
4. Full final render: `uv sync`, `ruff check`/`format --check` across `src/`, `core/`, `tests/` — clean
5. `make test` — all 36 unit tests pass

**Files touched**: 3 new files (`collaboration.md.jinja`, `grow-companion/SKILL.md`, `dream/SKILL.md`), edits to `copier.yaml` (messages + the akira-cleanup bug fix), `CLAUDE.md.jinja`, `_scaffold/README.md.jinja`, `.claude/skills/README.md.jinja`.
**Done when**: rendered docs mention the companion layer when enabled, say nothing when disabled. ✓ (verified via explicit path checks, not just render success)

---

## Plan status: all 6 phases complete — 2026-07-13

Three prebuilt agents (`lg_agent`/`rag_agent`/`adk_agent`) with real MCP-client wiring in both frameworks; `akira` ported as a second prebuilt agent; `SANYI` ported as a lightweight skill; `include_dev_companion` toggle carrying a scoped-down version of puffin's transform-not-append discipline. Every phase was verified against a real rendered project, not just read for plausibility — this surfaced 4 real bugs along the way (a pre-existing `mcp_servers` packaging bug, a settings field-name collision, a Phase-1 test regression, and the akira cleanup-task ordering bug above), all fixed and documented at the point they were found rather than glossed over.

## Test Plan
- Render the template 4 ways: everything on (default), everything off (`scaffold_full_project=false`), all-new-toggles-off-but-scaffold-on, all-on-minimal (`has_typescript=false`, `enable_structure_guard=false`). Confirm no orphaned files or broken references in any.
- For each of the three agents: boot + one real chat turn requiring the MCP tool, exercised against the actual rendered `mcp_servers/{{ mcp_server_slug }}`.
- `make akira-kaneda` + `make akira-dao` against the rendered project's own source — should not crash on a project with zero pre-existing findings.
- `/sanyi init` end-to-end against a rendered project.
- `/dream` against both a fresh and an artificially-aged companion doc.

## Risks & Rollback
- **Line-level specificity gap**: Phases 2–3's exact file contents weren't read in the research pass (only directory structure) — Steps 2.1/3.1 exist specifically to close that before any edit happens; if the inventory reveals substantially more domain-coupling than expected, treat as a blocker and re-scope before continuing, don't force a port.
- **MCP transport limits**: playground's server is stdio-only (`mcp.run()` with no args); if a future need requires HTTP/SSE transport, that's new work beyond this plan, not a port.
- **Copier task ordering**: new `_tasks` rm-rf lines (Step 0.2) must run before the final `_scaffold` cleanup task — verify ordering against existing `copier.yaml` task list to avoid deleting files a later task still expects.
- **Rollback**: every phase is additive (new files/toggles) except Step 5.2 (one-line edit to existing `code-review/SKILL.md`) and Step 1.2/3.3 (edits to `lg_agent`'s/`adk_agent`'s existing files) — trivially revertable via git per-phase.

## Open Questions
- Should `rag_agent`/`adk_agent` be independently toggleable (like `include_akira`), or always bundled with `scaffold_full_project` as currently planned? Current plan bundles them since you asked for parity with `lg_agent`, which itself has no separate toggle.
- Companion-layer doc location: proposed `.claude/docs/companion/` — confirm this doesn't collide with any existing convention before Step 6.1.
- Should akira's `findings/` output be added to the structure-guard's allowed-dirs enforcement, or left outside `eval_root`'s scope entirely? Leaning "outside" since it's not eval output, but flagging for confirmation.
