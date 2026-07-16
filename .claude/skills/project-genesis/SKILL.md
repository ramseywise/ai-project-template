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

### Step 0 — Check for existing DESIGN.md and planning docs

If a `DESIGN.md` or `.claude/docs/DESIGN.md` exists (produced by `/scope-poc`), read it first.
Also scan for planning docs that pre-answer infrastructure questions: `roadmap.md`,
`.claude/docs/milestones/*.md`, `.claude/docs/plans/*.md` — milestone files sometimes contain
the literal copier arguments (a live dry-run found `vector_backend=postgres` and
`primary_chat_agent=lg_agent` verbatim in a milestone's "done when"). Don't re-ask what's
already answered — but ratify inherited decisions out loud ("your milestone pins X — confirm?")
rather than silently adopting them. Surface only the questions that remain open.

If no DESIGN.md exists, consider suggesting `/scope-poc` before continuing — especially if the
user hasn't yet defined actors, MVP scope, or key architectural decisions. `/project-genesis`
works without it, but infrastructure choices made without a design are guesses.

### Step 1 — Ask, don't hand over a form

Have a short real conversation (not a rigid checklist read verbatim). It mirrors
`copier.yaml`'s own phased interview — scope first, implementation only where
Phase 1 makes it relevant:

**Phase 1 — scoping (always cover these):**

1. **What are you building, who's it for?** → `project_name`, `project_slug`,
   `project_description`, `project_type` (`chat_app`/`agent`/`workflow`/`rag`/
   `mcp_server`/`ai_backend`/`eval_suite`/`prototype`/`existing_repo` — the last
   one is layering-only mode: `.claude/` + whichever of `.agents/`/`mcp_servers/`
   they want, nothing else touched), `primary_users`
   (`internal`/`customers`/`developers`/`public_api`).
2. **What external systems does it touch?** → `external_systems` (multiselect:
   `slack`/`github`/`google_workspace`/`calendar`/`email`/`database`/`web`) —
   copier seeds integration and vector-store defaults from this, so get it right
   rather than skipping it.
3. **Backend language(s)** — Python (default) or a real TypeScript backend
   service too? → `primary_backend_language`.
4. **Where does it run?** → `deployment_target` (`local`/`docker`/`cloud`/`serverless`).
5. **Does it touch customer or otherwise sensitive data?** → `data_sensitivity`
   (`public`/`internal`/`restricted`/`secret`). Copier defaults this from
   `primary_users`, but don't let it default silently in conversation — it
   drives a hard rule in the generated `CLAUDE.md` and a Terraform tag.

**Phase 1b — the AI system itself (agent-shaped projects):**

6. **What tools will the agent use, will it store memory, does it need human
   approval before acting?** → `agent_tools` (multiselect; `mcp` seeds
   `include_mcp_server`), `agent_memory` (`none`/`conversation`/`long_term` —
   `long_term` seeds the postgres checkpointer), `human_approval`
   (`none`/`sometimes`/`always`). These land in DESIGN.md's Key Decisions —
   they matter more than any individual feature toggle.

**Phase 2/3 — only when the conversation raises them (otherwise the seeded
defaults are right):**

7. **Which chat agent(s)** — LangGraph (`lg_agent`), Google ADK (`adk_agent`),
   both, or neither (build on `rag_agent` alone)? → `primary_chat_agent`.
   Copier derives a sensible default from `project_type`; only ask if the
   design names a framework. `rag_agent` and `akira` ship regardless — they're
   shared LangGraph-based infra, not "the framework" being picked.
8. **Vector store at production scale, or just getting started?** →
   `vector_backend` (`duckdb` default / `memory` zero-setup / `opensearch`
   cluster / `postgres` pgvector — auto-defaulted to `postgres` when `database`
   is in `external_systems`).
9. **Optional add-ons** → `optional_features` (multiselect: `akira` +
   `dev_companion` default on; `promptfoo`/`ragas`/`web_research`/
   `meeting_intelligence`/`marketing`/`n8n_webhook`/`composio`/`ml_labs`).
   Mention only the ones the design implies — e.g. classical ML/stats work
   (baselines, forecasting, A/B) → add `ml_labs`.

Skip questions whose answer is obvious from context already given (e.g. if
they've already said "no existing repo, brand new thing", `project_type` can't
be `existing_repo`). Everything not covered keeps copier's own derived default
— don't invent additional questions, and don't ask about anything in
copier.yaml's "inferred, never asked" tier (`source_root`, `eval_root`,
`python_version`, `aws_region`, ...) unless the user brings it up.

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
  -d "project_type=<chat_app|agent|workflow|rag|mcp_server|ai_backend|eval_suite|prototype|existing_repo>" \
  -d "primary_users=<internal|customers|developers|public_api>" \
  -d "primary_backend_language=<python|typescript|both>" \
  -d "external_systems=[<slack, github, ...>]" \
  -d "deployment_target=<local|docker|cloud|serverless>" \
  -d "data_sensitivity=<classification>" \
  -d "agent_tools=[<search, mcp, ...>]" \
  -d "agent_memory=<none|conversation|long_term>" \
  -d "human_approval=<none|sometimes|always>" \
  -d "optional_features=[<akira, dev_companion, ...>]" \
  . "<output_dir>"
```

Drop any `-d` the conversation didn't cover — `--defaults` fills it from the
seeded derivations. Multiselects take YAML list syntax (`[a, b]`). Hidden/
derived variables (`scaffold_full_project`, `include_*`, `vector_backend`
when not asked, `source_root`, ...) can still be pinned with `-d` when the
conversation explicitly named them.

**Prefer a data file over a long `-d` chain.** With more than ~5 answers, write
them to a YAML file and pass `--data-file` — a 15-flag shell line is where
operator errors live (a live dry-run lost a cycle to a dropped positional arg):

```bash
cat > /tmp/genesis-answers.yml <<'EOF'
project_name_input: <name>
project_type: agent
external_systems: [database, calendar]
# ...one key per answer from Step 2's table
EOF
copier copy --vcs-ref HEAD --trust --defaults --data-file /tmp/genesis-answers.yml . "<output_dir>"
```

**Rendering into an existing repo** (files already present) needs a protocol, not
hope:
1. Before rendering: `git status` the target; snapshot any UNTRACKED files that the
   template will touch (`README.md`, `.claude/**`) to a backup dir — git cannot
   restore untracked files.
2. Render with `--overwrite` (non-interactive conflict prompts fail otherwise).
3. After rendering: restore user-owned files the template clobbered — at minimum
   `git checkout -- README.md` if the repo had a real README — and report exactly
   which pre-existing files were overwritten vs preserved.

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

- **Tell the user the add-later story in Step 5's report — always.** The render is
  not a one-shot commitment: `.copier-answers.yml` in the generated project records
  every answer, and any toggle can be flipped later by re-running copier against the
  same directory with the changed answer (`copier copy --overwrite -d include_ml_labs=true ...`,
  or `copier update` once the template is version-tagged). Users who don't know this
  over-scaffold "just in case" — say it explicitly so they can scaffold the MVP and
  add capabilities when they're actually needed.
- **Legacy toggle → new axis mapping** (planning docs written against the old flat
  interview stay actionable — both forms are honored by `-d`):

  | Old toggle | New interview source |
  |---|---|
  | `include_calendar_integration=true` | `calendar` in `external_systems` |
  | `include_meeting_intelligence=true` | `meeting_intelligence` in `optional_features` |
  | `include_ml_labs=true` | `ml_labs` in `optional_features` |
  | `include_promptfoo/ragas/web_research/composio/n8n_webhook` | same name in `optional_features` |
  | `scaffold_full_project=false` | `project_type=existing_repo` |

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
