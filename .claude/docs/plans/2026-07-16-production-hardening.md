# Plan: production_hardening
Date: 2026-07-16
Status: EXECUTED
Based on: direct codebase inspection (no research doc — gaps identified against
`.claude/docs/plans/2026-07-14-template-backlog.md`'s completed state)

## Goal

Close the four production-quality gaps that remain after the 2026-07-14 backlog pass:
no version control, shallow CI coverage, design metrics that never reach the eval
harness, and a missing naive-baseline question in the scoping interview.

## Approach

Harden what exists rather than adding surface area. CI grows from render+lint on 5
configs to a two-tier matrix (render+lint everywhere, real test execution on one config
per feature axis). The `/scope-poc` → `/project-genesis` pipeline gains the two Ben
Wilson planning disciplines it's missing — a naive-baseline question and an Evaluation
section with concrete metric targets — and those targets get a real landing spot in the
generated project (`evals/targets.yaml` + a threshold gate in the eval runner), so the
design artifact binds the build instead of decorating it. Key tradeoff: CI test
execution is scoped to one config per axis, not the full cross-product — the
cross-product is combinatorially large and the backlog showed bugs cluster per-axis
(staging-path mistakes, dependency gating), not in axis interactions.

## Baseline

- `git status`: repo has **zero commits**; all 287 files untracked. No tags.
- No test suite at template-repo root — verification is render + run inside renders
  (the backlog's established discipline).

## Out of Scope

- Workstream B: the live end-user dry-run of `/scope-poc` → `/project-genesis`
  (separate interactive session — cannot be done by an agent).
- Any new copier toggles, integrations, or scaffold content beyond `evals/targets.yaml`.
- Porting puffin `/genesis` features (explicitly ruled out in
  `puffin-integration/plan.md` — genesis SKILL.md restates this).
- LLM-judge graders beyond the existing optional ragas toggle.
- Template-repo-level `.pre-commit-config.yaml` / `renovate.json` (backlog #6 already
  triaged these as low priority).
- Real W&B / OpenSearch / Anthropic API verification (no keys/cluster in this
  environment — same boundary class as the backlog).
- CI for the *generated* project (`_scaffold/.github/` has only a PR template today) —
  the eval gate lands as a Makefile target; wiring it into generated-project CI is a
  follow-up.

## Steps

### Step 0: Initial commit + tag — USER ACTION, blocks everything ⏳ PENDING (only remaining item)

**Files**: none (git only)
**What**: You (not Claude — per global rules) make the initial commit and tag it, so
copier consumers can pin versions and `copier update` works, and so every later step
has a rollback point.
**Command**:
```bash
cd ~/workspace/ai-project-template
git add -A && git commit -m "chore: initial commit — template through backlog pass 2026-07-14"
git branch -m master main   # CI triggers on main
git tag v0.1.0
```
**Done when**: `git log --oneline` shows one commit; `git tag` shows `v0.1.0`;
branch is `main`.

### Step 1: CI — two-tier matrix with real test execution ✓ DONE — 2026-07-16

**Files**: `.github/workflows/test-render.yml` (all 59 lines)
**What**: Keep the existing 5 render+lint configs; add `workflow_dispatch` trigger.
Add one **full-tier** config per feature axis, each running the render's own test
suite, not just lint:

| Config | Extra args | Test tier |
|---|---|---|
| defaults-tested | *(none)* | `uv sync --group dev && uv run pytest` |
| ts-backend | `-d primary_backend_language=typescript` | npm install/lint/typecheck/test/build in `render-test/` |
| split-service | `-d primary_backend_language=both -d frontend_backend_topology=split_service` | pytest (backend) + npm install/build (frontend) |
| ml-labs | `-d include_ml_labs=true` | pytest (includes the 30 labs tests) |
| mcp-ts | `-d mcp_server_language=typescript` | npm install/build in `mcp_servers/render-test/` |
| vector-memory | `-d vector_backend=memory` | pytest |

**Snippet** (matrix entry shape — a `tier` key drives conditional steps):
```yaml
# before: every entry is render+lint only
- name: primary_chat_agent-lg_agent
  args: "-d primary_chat_agent=lg_agent"
# after: entries gain a tier; steps gate on it
- name: ts-backend
  args: "-d primary_backend_language=typescript"
  tier: test-ts
...
- name: Run Python tests
  if: matrix.tier == 'test-py'
  working-directory: out
  run: uv sync --group dev && uv run pytest -q
```
Enable uv/npm caching (`astral-sh/setup-uv@v3` with `enable-cache: true`,
`actions/setup-node@v4` with `cache: npm` — note npm cache needs a lockfile; renders
have none, so skip npm caching if it errors rather than fighting it).
**Test**: `act` is not assumed — validate YAML locally (`python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/test-render.yml'))"`),
then real verification is the first push to GitHub (Step 6 note).
**Done when**: workflow YAML parses; matrix contains 11 entries; every full-tier
config's commands have been run locally against a fresh render (Step 6).

### Step 2: scope-poc — naive-baseline question ✓ DONE — 2026-07-16

**Files**: `.claude/skills/scope-poc/SKILL.md` (Step 3, lines 86–95; DESIGN.md
structure, lines 152–216), `template/DESIGN.md.jinja` (lines 14–18)
**What**: Add question **8b** to Tier 3: *"What's the naive baseline? What happens if
you build nothing — or solve it with a lookup table / keyword search / a human
checklist? What must the AI beat, and by how much, to justify itself?"* Add a
matching `**Naive baseline:**` line to the DESIGN.md structure's Problem section and
to `DESIGN.md.jinja`.
**Snippet** (`DESIGN.md.jinja`):
```markdown
# before
**POC demo target:** <!-- What does someone see in a 5-minute demo... -->
# after
**POC demo target:** <!-- What does someone see in a 5-minute demo... -->

**Naive baseline:** <!-- What's the non-AI alternative (do nothing / keyword search /
manual process), and what must the AI beat to justify itself? -->
```
**Test**: `make new_project_dev`-style render into scratch dir; grep the rendered
`DESIGN.md` for `Naive baseline`.
**Done when**: both files carry the section; rendered DESIGN.md has no leftover Jinja.

### Step 3: DESIGN.md — Evaluation section with metric targets ✓ DONE — 2026-07-16

**Files**: `.claude/skills/scope-poc/SKILL.md` (Step 3 lines 92–95, DESIGN.md
structure lines 152–216, handoff table lines 135–148), `template/DESIGN.md.jinja`
**What**: Promote Step 3's "How will you evaluate good?" from prose into a concrete
artifact: a new `## Evaluation` section in the DESIGN.md structure — a table of
(metric, target, how measured), seeded from the risks in Tier 5 Q13 ("top 2–3 risks
become the eval suite's primary grading targets" — currently asserted, never
materialized). Add a row to the Step 7 handoff table: `Evaluation targets →
evals/targets.yaml`.
**Snippet** (DESIGN.md structure addition):
```markdown
## Evaluation

| Metric | Target | How measured |
|--------|--------|--------------|
| hit_rate | ≥ 0.8 | `make eval-heuristic` vs golden set |
| <!-- risk-derived metric --> | | |

<!-- These become evals/targets.yaml in the generated project — the eval gate
     fails when a metric drops below target. -->
```
**Test**: same render + grep as Step 2.
**Done when**: structure, jinja stub, and handoff table all carry Evaluation;
render clean.

### Step 4: evals/targets.yaml + threshold gate in the eval runner ✓ DONE — 2026-07-16

**Files**: new `template/_scaffold/{{ eval_root }}/targets.yaml`,
`template/_scaffold/{{ eval_root }}/pipelines/run.py.jinja` (imports lines 19–37;
`run_heuristic` lines 214–311; `main` lines 432–448),
`template/_scaffold/Makefile.jinja` (eval targets block)
**What**: Ship a commented `targets.yaml` (keys: `hit_rate`,
`mean_reciprocal_rank`, optional `mean_answer_overlap`; default targets commented
out so a fresh project doesn't fail before it has a real golden set). In
`run.py.jinja`: `_load_targets()` (returns `{}` if file missing/empty — same
graceful-degradation contract as `_try_log_to_wandb`), `_check_targets(report)`
printing per-metric PASS/FAIL, and a `--gate` flag on the `heuristic` subcommand
that exits 1 on any FAIL. New Makefile target `eval-gate` = `heuristic --gate`.
No gate → behavior identical to today.
**Snippet**:
```python
# after (run_heuristic tail)
_print_summary(backend, report)
failures = _check_targets(report, _load_targets())   # prints PASS/FAIL lines, [] if no targets
_try_log_to_wandb(backend, report)
return report, failures
```
`yaml` parsing via stdlib-adjacent `pyyaml` — already a transitive dep, but declare
it explicitly in `pyproject.toml.jinja` (same disclosure standard as
`sentence-transformers` per backlog #1).
**Watch for**: this file is already `.jinja` — any literal `{{ }}` in added code must
sit inside the existing `{% raw %}` discipline (backlog #2 bug 1).
**Test**: fresh render → `uv sync` → `make corpus-ingest && make rag-corpus-ingest &&
make eval-heuristic` (unchanged behavior, no targets) → uncomment a
`hit_rate: 0.99`-style unreachable target → `make eval-gate` exits 1; set
`hit_rate: 0.5` → exits 0. `uv run pytest` still green.
**Done when**: both gate outcomes demonstrated for real; ruff + pytest clean;
no leftover Jinja.

### Step 5: project-genesis — carry DESIGN.md and targets into the render ✓ DONE — 2026-07-16

**Files**: `.claude/skills/project-genesis/SKILL.md` (Step 4 lines 95–121, Step 5
lines 123–131)
**What**: Today a project scaffolded after `/scope-poc` still gets the *blank*
`DESIGN.md` stub — the real design never lands in the generated repo. Add to Step 4:
after copier succeeds, if a pre-scaffold DESIGN.md was found in Step 0, copy it over
`<output_dir>/DESIGN.md` (reconciling the `data_sensitivity` line with the copier
answer if they disagree — flag, don't silently pick one). If the design has an
Evaluation table, transcribe its targets into `<output_dir>/evals/targets.yaml`.
Step 5's report lists both actions.
**Snippet** (SKILL.md addition, Step 4 tail):
```markdown
After a successful render: if Step 0 found a DESIGN.md, copy it over
`<output_dir>/DESIGN.md` (the rendered stub is blank — the real design wins), and
transcribe its Evaluation table into `<output_dir>/evals/targets.yaml`. If the
design's data classification disagrees with the `data_sensitivity` answer just
rendered, stop and ask — don't reconcile silently.
```
**Test**: doc-only change — verify by walking the skill once against a scratch
DESIGN.md + render (part of Step 6).
**Done when**: skill instructs the carry-over + reconciliation; Step 7 handoff table
in scope-poc (Step 3 above) and this skill agree on the `targets.yaml` contract.

### Step 6: End-to-end verification pass ✓ DONE — 2026-07-16

**Files**: none (verification only)
**What**: The backlog's discipline — render + install + run, not render-only — applied
to every config Step 1 promises CI will test:
1. Six full-tier renders into scratch dirs; run each tier's exact CI commands locally.
2. One combined render (`ml_labs` + `typescript` + `mcp ts`) as a smoke test of axis
   interaction in `_tasks` staging order.
3. The Step 4 gate demonstration (both exit codes).
4. `pre-commit run --all-files` on the defaults render (regression check on backlog #6).
**Test**: the commands above.
**Done when**: all pass locally. First GitHub push (user action) confirms the
workflow runs green remotely — CI has never actually executed (repo has no remote/commits).

## Test Plan

- Per-step tests as listed; Step 6 is the integration gate.
- Nothing merges to the template without: render clean (no leftover Jinja), `ruff
  check` + `format --check` clean on rendered Python, tier-appropriate test suite
  green, and — for Step 4 — both gate outcomes observed for real.

## Risks & Rollback

- **CI runtime/cost**: `uv sync` pulls torch via `sentence-transformers` (~2–3 GB).
  Mitigation: uv cache enabled; full tier limited to 6 of 11 configs. If still too
  slow, demote `vector-memory` and `split-service` to render+lint.
- **Jinja/f-string collisions** editing `run.py.jinja` (backlog #2 bug 1 recurrence).
  Mitigation: render + grep for `{{` after every edit, per existing CI check.
- **`_tasks` staging-order bugs** — not touched by this plan (no new toggles), but
  Step 6's combined render guards against regressions anyway.
- **Rollback**: after Step 0 exists, every step is one `git revert` away. That's the
  point of Step 0.

## Execution record — 2026-07-16

Steps 1–6 executed and verified; Step 0 (initial commit + tag) remains a user action.
Pre-edit copies of every touched file: scratchpad `pre-hardening-snapshot/` (the
revert path until Step 0 exists).

**Verified for real** (render + install + run, per backlog discipline): 7 configs
render Jinja-clean; lint-check + pytest green on defaults/ml-labs/vector-memory/
split-service (36/66/36/36 tests); full npm chain green on ts-backend; install+build
green on TS MCP server and split_service Next.js frontend; `make eval-heuristic`
behavior unchanged with targets commented out; `make eval-gate` exits non-zero on an
unreachable target (per-backend FAIL lines) and 0 on an achievable one; `pre-commit
run --all-files` passes on a defaults render; combined render (ml_labs + both +
mcp ts) stages all three axes correctly.

**Deviations** (all declared during execution):
1. CI leftover-Jinja grep now excludes `.agents/` — vendored
   `framework-selection/SKILL.md` mentions `{{ ts_project_root }}` in prose in every
   render; renaming it `.jinja` would crash defaults renders (variable undefined when
   `has_typescript=false`). Same vendored-material precedent as LINT_PATHS/pre-commit.
2. CI lint step delegates to the render's own `make lint-check` instead of repo-wide
   `ruff check .` — vendored `.claude/skills/mcp-builder/scripts/` fails repo-wide
   ruff (pre-existing; the old workflow had never actually run — no remote/commits).
3. Unlisted files fixed (real template bugs, found by running lint on renders):
   `_scaffold/src/agents/{lg_agent,rag_agent}/main.py` — I001 on the split_service
   CORS import block. Root cause: ruff classifies `middleware` first-party only when
   `src/middleware` exists, so the same bytes can't lint clean in both configs.
   Fixed properly via `known-first-party = ["middleware"]` in `pyproject.toml.jinja`
   (imports themselves restored to original form).
4. Unlisted file fixed: `_scaffold/src/middleware/auth.py.jinja` — three UP045
   `Optional[...]` violations (the split_service tier post-dates the backlog's last
   full lint pass and had never been lint-verified in a render).

**Re-verification after the copier.yaml phased-interview rework (2026-07-16, second
pass)**: the interview rework (project_type/primary_users/external_systems/agent_tools/
optional_features, landed after the first execution pass) kept every `include_*` toggle
pinnable via `-d`, so the CI matrix stayed valid. Workflow updates: trigger on
`master` too (repo's actual branch), layering-only entry now uses the canonical
`-d project_type=existing_repo`, two new render-tier entries for `project_type=
mcp_server`/`eval_suite` (13 matrix entries total), and the leftover-Jinja check
excludes `promptfoo.config.yaml` ({{prompt}}/{{question}} are promptfoo's own runtime
syntax — eval_suite now auto-enables promptfoo and would have failed CI). Full battery
re-run green against the reworked template: 9 configs render Jinja-clean; lint+pytest
green on defaults/ml-labs/vector-memory/split-service/mcp_server-type/eval_suite-type
(36/66/36/36/17/17); npm chains green (ts-backend, TS MCP, split frontend); gate
demo re-confirmed (non-zero / zero).

**Code-review fix pass (2026-07-16, after /code-review production_hardening)**: of the
10 reported findings, 6 fixed and verified by fresh renders; findings 4–6 and 10
(vector_backend reachability, web_research/composio auto-seeding, eval_suite's
implicit MCP server, SKILL.md enum duplication) left as design decisions. Fixes:
(1) `has_typescript` re-gated on scaffold_full_project — layering renders ship 0
ts hooks, full TS renders still ship 3; (2) `include_akira`/`include_dev_companion`
gated on scaffold_full_project AND their `_tasks` guards changed from
`(not scaffold_full_project) or include_*` to `include_*` — layering renders no
longer ship akira/dream/grow-companion skills or companion docs; (3) BONUS
pre-existing bug found while verifying: `ts_lint.sh`'s task guard had the same
short-circuit class and leaked the hook into every layering render (even
Python-only) — fixed with the positive-condition guard; (4) leftover-Jinja CI
check no longer excludes promptfoo.config.yaml wholesale — {{prompt}}/{{question}}
filtered by pattern so the file's real copier substitutions stay checked; (5) new
hidden `is_agent_shaped` predicate replaces 4 copies of the agent-shaped
project_type list (3 when: clauses + DESIGN.md.jinja); (6) CI lint step syncs only
the dev group (`uv sync --only-group dev` + `UV_NO_SYNC=1 make lint-check`) —
verified 2.5s on a fresh render vs a full agent-runtime install; test-tier jobs
still full-sync via `uv run pytest`; (7) redundant `defaults` render-only matrix
row dropped (subsumed by defaults-tested; 12 entries).

**Process note**: one verification round was invalidated and redone — zsh doesn't
word-split unquoted `$args`, so a render loop silently dropped every `-d` flag and
rendered 7× defaults. Caught by auditing rendered toggle markers, not render success;
all configs re-rendered with explicit args.

## Open Questions

1. Tag scheme: `v0.1.0` assumed — bump to `v1.0.0` if you consider the backlog pass
   "1.0 done"?
2. Should `defaults-tested` full tier also run the real ingest→eval chain in CI
   (downloads the embedding model, ~90s + cache)? Plan says pytest-only; e2e chain
   stays a local/Step 6 concern.
3. GitHub remote: none configured. CI is unverifiable until you create the repo and
   push — fine to do at Step 0 or after Step 6?
