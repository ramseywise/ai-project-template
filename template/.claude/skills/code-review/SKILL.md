---
name: code-review
description: "Standing repo/workspace review — no plan doc required. Leveled: level:1 diff+lint+doc-flags, level:2 (default) +tests+SANYI diff+akira-scan, level:3 +full sanyi audit (single repo only). Pass repo:<name> for one repo, 'sweep' for all dirty workspace repos, 'headless' for non-interactive runs (questions go to a Needs-input section). For plan-fidelity review of a specific work item, use /code-review instead."
disable-model-invocation: true
allowed-tools: Read Grep Glob Bash Write Agent
skills: [review-shared]
---

You are a staff engineer running a standing review. Report-only for code (never fix
findings inline); direct and specific; real problems only — style is the linter's job.

## Routing

Parse `$ARGUMENTS` (order-independent tokens):
- `repo:<name-or-path>` — target one repo (bare name → `~/workspace/<name>`)
- `sweep` — target every `~/workspace/*` repo where `git -C <repo> status --porcelain`
  is non-empty (list them and confirm before running if more than 4)
- `level:1|2|3` — review depth (default 2). Each level contains the previous:
  - **1** (cheap): diff scope + mechanical lint + doc flags. No agents, no tests,
    no sanyi.
  - **2** (standard): + tests + SANYI diff review + akira-scan + machine-doc
    proposed diffs.
  - **3** (deep): + full `/sanyi audit` of the whole repo. Single-repo ONLY —
    refuse `sweep` at level 3.
  - `fast` = alias for `level:1`.
- `headless` — non-interactive run (invoked via `claude -p`): NEVER ask the user
  anything; clarifying questions and approval-needed items go into a `### Needs input`
  section of the report; always finish by writing the report.
- Neither `repo:` nor `sweep`: the repo containing cwd; if cwd is not inside a project
  repo, ask — never default silently (headless: report the ambiguity and stop).

Hard rule: exactly 3 levels, no sub-flags — a new need is a new level or nothing.

Run everything with the target as working dir (`git -C`, `cd <repo> && ...`). Repeat the
full pipeline per repo; one report per repo.

## Pipeline (per repo)

### 1. Diff scope
`git -C <repo> status --porcelain` + `git -C <repo> diff main...HEAD --name-only`
(fall back to `master` or the default branch). Union of branch-changed + staged +
unstaged files = the changed set. Empty set → report "clean" and move on.

### 2. Mechanical — delegate to the repo's own tooling
Probe: `make -C <repo> -n lint 2>/dev/null` / `make -C <repo> -n test 2>/dev/null`.
- Targets exist → run them (`make lint` at all levels; `make test` at level ≥2).
- No Makefile targets → fallback by stack: Python `uv run ruff check .` +
  `uv run pytest --tb=short -q` (level ≥2); TS `npm run lint` + `npm test`
  (level ≥2), only if those scripts exist in package.json.
Never install anything. Record pass/fail; test failures don't abort the sweep — they
lead the report.

### 3. Contract (SANYI) — level ≥2
If `SANYI.md` exists at the repo root: run the `/sanyi review` protocol on the changed
set — glob-match changed files against the contract registry, report NEW violations
only (entries in `## Debt` stay silent). SANYI outputs canonical schema fields alongside
its native report (see `~/.claude/refs/finding-schema.md`). Merge-impact mapping:
BY-* → `blocker`, JY-* → `important`, BN-1 → `suggestion`, MG-*/UN-* → `nit`.
Report-only — never auto-fix a contract violation. Skip silently when no `SANYI.md` exists.
At **level 3** additionally run the full `/sanyi audit` protocol on the whole repo
(not just the diff) — this is the expensive step and why level 3 is single-repo.

### 4. Quality scan (akira-scan) — level ≥2
Split the changed set into batches of ~5 files. Spawn the global `akira-scan` agent on
each batch **in parallel** (pass file paths + one-line repo context; `model: haiku` —
pinned in the agent def, restate on the Agent call). Agent outputs canonical schema
with evidence tags (see `~/.claude/refs/finding-schema.md`).

**Merge step** (per `review-shared` merge logic): collect all akira-scan + SANYI findings
in canonical schema format. Group by file+lines overlap (within 5 lines) AND category
similarity. Judge if grouped findings describe the same underlying issue. Merge confirmed
duplicates: preserve all source IDs, use most precise root cause, take higher merge_impact,
take more certain evidence_state. Drop findings the linter already caught in step 2.
Rank blockers first, then important, questions, suggestions, nits.

### 5. Docs
- Machine-consumed docs (`.claude/`, CLAUDE.md, SANYI.md): if changed code contradicts
  them (renamed commands, moved paths, dead references), FLAG at level 1; PROPOSE a
  diff in the report at level ≥2.
- Human-consumed docs (README, DESIGN.md, wiki): at level ≥2, run the `/docs-check`
  protocol (diff mode — scoped to changed dirs). Flag staleness only — never edit
  (doc-writer boundary, `~/.claude/rules/docs.md`). At level 1, skip structural check
  but still flag obviously broken references caught by the `docs_hygiene` hook.

### 6. Report
If the repo has a plan doc with `Status: IN PROGRESS` whose scope covers this diff,
append there; otherwise write `<repo>/.claude/docs/plans/YYYY-MM-DD-review-sweep.md`
(`Status: EXECUTED` once written).

```markdown
## Review — sweep [date]

### Mechanical
- Lint: PASS/FAIL  ·  Tests: PASS/FAIL/SKIPPED (fast)

### Findings (ranked, canonical schema)
- **[blocker:verified]** `AK-001` `file:line` — claim title
  Evidence: basis · Merge impact: blocker
- **[important:supported]** `SY-001 + AK-003` `file:line` — merged finding
  Evidence: basis · Merge impact: important
- **[nit:verified]** ...

### Contract (SANYI)
[findings with canonical schema fields or "no contract" / "no new violations"]

### Docs
- Proposed diffs (machine-consumed): ...
- Flags (human-consumed): ...

### Verdict
**approve** | **needs-changes** | **clean**
[1-line rationale. If needs-changes: list blocking finding IDs.]
```

In `sweep` mode, finish with a one-line-per-repo summary table (repo · lint · tests ·
blocking count · verdict) in the session output — not written to any file.

## Boundaries

- Never commit, push, or fix findings — Ramsey commits; fixes go through normal work.
- Never edit human-consumed docs.
- Per-repo failures (missing tooling, broken make) are reported, not worked around.
- See `/akira` for the question (`wander`) and fix (`dao`) modes — the interactive,
  actuating sibling that shares this scan.
