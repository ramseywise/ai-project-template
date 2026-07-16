---
name: project-genesis
description: >
  Scope a new AI project through a short real conversation, then run this
  template's copier non-interactively to scaffold it — instead of answering
  ~20 raw copier prompts blind. Triggers on: "new ai project", "scaffold a
  project from this template", "start a new agent project", "/project-genesis".
---

# /project-genesis

Thin orchestrator around this repo's own `copier.yaml` — same spirit as
`template/.claude/skills/new-agent/SKILL.md` (ask real questions, confirm
before acting, don't silently default), scoped much narrower than puffin's
`/genesis`. This is a **project-scoping-to-copier-answers translator**, not an
identity-emergence protocol — no multi-phase engagement ritual, no identity
files. That distinction is deliberate: see
`.claude/docs/in-progress/puffin-integration/plan.md`'s "Out of Scope" section,
which already decided against porting puffin's genesis verbatim into this
template. If you're tempted to add phases, growth logs, or reflection steps
here, that's scope creep back toward the thing that was explicitly ruled out —
don't.

## Usage

```
/project-genesis [--output path/to/dir]
```

| Arg | Default | Description |
|-----|---------|-------------|
| `--output` | ask the user | Where to render the project (existing or new dir) |

## Steps

### Step 0 — Check for existing DESIGN.md

If a `DESIGN.md` or `.claude/docs/DESIGN.md` exists (produced by `/scope-poc`), read it first.
Many of the infrastructure questions below are determinable from the design — don't re-ask what's
already answered. Surface only the questions that remain open after reading the design doc.

If no DESIGN.md exists, consider suggesting `/scope-poc` before continuing — especially if the
user hasn't yet defined actors, MVP scope, or key architectural decisions. `/project-genesis`
works without it, but infrastructure choices made without a design are guesses.

### Step 1 — Ask, don't hand over a form

Have a short real conversation (not a rigid checklist read verbatim) covering:

1. **What are you building, who's it for?** → `project_name`, `project_slug`,
   `project_description`.
2. **Fresh project, or layering onto something that already exists?** → maps to
   `scaffold_full_project` (false = layering-only: `.claude/` + whichever of
   `.agents/`/`mcp_servers/` they want, nothing else touched).
3. **Does it touch customer or otherwise sensitive data?** → `data_sensitivity`
   (`public`/`internal`/`restricted`/`secret`). Don't default this silently —
   it drives a hard rule in the generated `CLAUDE.md` and a Terraform tag.
4. **Does it need retrieval/eval rigor** (RAG, agent evals, anything graded
   against a golden set)? → `enable_structure_guard`.
5. **Frontend/TypeScript component?** → `has_typescript`.
6. **Does it need to expose tools to other agents/services?** → `include_mcp_server`
   (+ `mcp_server_name`/`mcp_server_slug` if yes).
7. **Which chat agent(s) do you want** — LangGraph (`lg_agent`), Google ADK
   (`adk_agent`), both (today's default), or neither (build your own on top of
   `rag_agent` alone)? → `primary_chat_agent`. Note `rag_agent` (the retrieval
   backend the MCP tool calls) and `akira` ship regardless of this choice — they're
   shared LangGraph-based infra, not "the framework" being picked.
8. **Backend language(s)** — Python (default) or a real TypeScript backend
   service too? → `primary_backend_language`. Independent of `mcp_server_language`
   (the MCP server's own implementation language).
9. **Vector store at production scale, or just getting started?** → `vector_backend`
   (`duckdb` default / `memory` for zero-setup dev / `opensearch` for a real cluster).
10. **Any classical ML/stats work** (baseline model comparison, forecasting,
    A/B testing) **alongside the agentic-AI pieces?** → `include_ml_labs`
    (default `false` — this is a large, separate addition, don't default it on).

Skip questions whose answer is obvious from context already given (e.g. if
they've already said "no existing repo, brand new thing", don't re-ask
`scaffold_full_project`). Everything not covered by these seven questions keeps
copier's own default — don't invent additional questions.

### Step 2 — Map to copier variables

Build the `-d key=value` list from Step 1's answers. Leave anything not
explicitly discussed unset — it'll fall through to `copier.yaml`'s own default
via `--defaults` in Step 4.

### Step 3 — Confirm before acting

Show the derived answer table back to the user (variable → value → why) before
running anything. If an answer feels like a guess rather than something they
actually said, ask directly instead of assuming — same discipline as
`new-agent/SKILL.md`'s "don't silently default."

### Step 4 — Execute non-interactively

From this repo's root:

```bash
copier copy --vcs-ref HEAD --trust --defaults \
  -d "project_name_input=<name>" \
  -d "project_slug=<slug>" \
  -d "project_description=<description>" \
  -d "data_sensitivity=<classification>" \
  -d "scaffold_full_project=<true|false>" \
  -d "enable_structure_guard=<true|false>" \
  -d "has_typescript=<true|false>" \
  -d "include_mcp_server=<true|false>" \
  -d "primary_chat_agent=<lg_agent|adk_agent|both|none>" \
  . "<output_dir>"
```

Resolve `<output_dir>` to an absolute path first (`mkdir -p` then `cd ... && pwd`)
— a relative path here has previously caused a broken `mv` mid-render (see
`Makefile`'s `run_copier` target, which now does this resolution for the
`make new_project`/`make new_project_dev` path; this skill must do the same
since it calls `copier` directly rather than through `make`).

`--vcs-ref HEAD` renders from the working tree (including uncommitted changes,
with copier's own `DirtyLocalWarning`) rather than requiring a commit first —
this was verified working end-to-end against this exact repo state.

After a successful render: if Step 0 found a DESIGN.md, copy it over
`<output_dir>/DESIGN.md` (the rendered stub is blank — the real design wins), and
transcribe its Evaluation table into `<output_dir>/evals/targets.yaml` (uncomment/
add one `metric: target` line per table row whose metric the eval runner measures;
metrics it doesn't measure stay in DESIGN.md only — name them in the Step 5 report
as manual-grading targets). If the design's data classification disagrees with the
`data_sensitivity` answer just rendered, stop and ask — don't reconcile silently.

### Step 5 — Report

Summarize what was generated (directory tree, notable toggles that ended up
on/off), report whether a DESIGN.md was carried over and which Evaluation
targets landed in `evals/targets.yaml` (vs. manual-grading targets that stayed
in DESIGN.md only), and surface the template's own next steps (mirrors `_message_after_copy`
in `copier.yaml`: review `CLAUDE.md`'s Hard Rules, `chmod +x .claude/hooks/*.sh`
if needed, `make setup` then whichever of `make lg-up`/`make adk-up`/`make rag-up`
matches `primary_chat_agent` if `scaffold_full_project`, `uv sync` inside
`mcp_servers/<slug>` if `include_mcp_server`, and `/sanyi init` to define the
project's change-contract now that its shape is set).

## Notes

- The raw `make new_project` (interactive) / `make new_project_dev` (dirty
  working tree, no commit required) targets in this repo's `Makefile` remain
  the power-user/CI/scriptable path — this skill doesn't replace them, it's a
  friendlier front door for the common case.
- If the conversation reveals a need this template genuinely can't scaffold
  (a capability with no corresponding copier toggle), say so explicitly rather
  than silently dropping it — same reporting discipline as `new-agent`'s Step 4.
- **Recommended sequence:** `/scope-poc` (design interview → DESIGN.md) → `/project-genesis`
  (infrastructure interview → copier). Running `/project-genesis` alone is valid but means
  infrastructure choices are made without design context. The generated project includes a
  blank `DESIGN.md` stub as a reminder to fill it in.
