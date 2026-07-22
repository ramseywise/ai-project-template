---
name: workflow-retro
description: "Tooling retrospective — closes the context-engineering feedback loop (observe → diagnose → codify → enforce → verify). Includes config-health audit (duplicate skills, settings syntax, memory staleness, plan-doc hygiene). Reads session friction signals, the tooling ledger, guacamayo growth entries, and plan-doc deviations; emits proposed diffs to hooks/skills/rules grouped by write target, then applies the ones you approve. Trigger on: /workflow-retro, 'retro', 'tooling retrospective', 'what friction keeps recurring', 'config audit', 'audit settings'."
disable-model-invocation: true
allowed-tools: Read Grep Glob Bash Edit Write
---

You are running a tooling retrospective. Steps 0–4 produce **proposed diffs** and apply
nothing. Step 5 applies only the diffs Ramsey explicitly approves — no approval, no write.
Identity files (`.sounding/`) are never touched at any step; reflect/synthesize own that
space, and this loop only *flags* graduation candidates there.

## Step 0 — Verify before proposing (read the ledger first)

Read `~/workspace/guacamayo/.claude/docs/tooling-ledger.md`. Every row with status `hypothesis` is your top
queue item. For each:

1. **Check the Metric column first.** Rows with a typed metric (`absence:`, `count-drop:`,
   `presence:`, `ratio:`) have a machine-checkable signal — look for that signal in session
   data (insights dry-run output, hook logs, session JSONL patterns). Rows with `—` (legacy,
   pre-tracker) fall back to manual evidence search.
2. Find evidence the motivating friction stopped or recurred since the change (session
   transcripts, hook logs, repeated manual corrections). Verification is concrete —
   "did the friction stop", with a session reference — not vibes.
3. Propose the row update: `hypothesis → verified (evidence)` or `hypothesis → failed (evidence)`.
   A failed row is itself a finding (the fix didn't take; diagnose why).

## Step 0.5 — Config health (mechanical checks)

Run these checks across the workspace. Findings enter Step 2 as findings like any other,
tagged with severity (BLOCKER / WARN / NOTE).

**Check A — Config-layering duplicates (BLOCKER).** For every repo in `~/workspace` with a
`.claude/`, check for skills/hooks that duplicate a global one by name. Same name in repo
AND global → BLOCKER (double-load + drift). Exception: repo skills documented as
deliberately divergent in that repo's CLAUDE.md. Known-sanctioned repo-local sets:
guacamayo identity-lifecycle (wake/grow/dream/genesis), repo project skills.

**Check B — Settings schema (BLOCKER/WARN).** For `~/.claude/settings.json` and every repo
settings file: (1) JSON validates, (2) wildcard syntax uses `Bash(cmd:*)` not
`Bash(cmd *)`, (3) tool names in Allow/Deny/Ask rules exist (stale: `Task`→`Agent`,
`SlashCommand`→`Skill`, `TodoRead`), (4) no secrets in settings.

**Check C — Memory staleness (WARN).** Read project memory files; flag stale state,
duplicates, contradictions with current CLAUDE.md.

**Check D — Doc artifacts (NOTE).** Flag leftover `RESEARCH.md`/`PLAN.md`/`SESSION.md` or
`in-progress/` dirs for migration to `plans/YYYY-MM-DD-<slug>.md`.

**Check E — Plan-doc hygiene (NOTE).** Flag plan docs missing `Status:` lines.

**Check F — Skill name alignment (NOTE).** For every skill dir, verify `name:` in SKILL.md
frontmatter matches the directory name. Mismatches break `/slash` dispatch silently.

## Step 1 — Observation sources

Read what exists; skip gracefully what doesn't. Note which sources you actually used.

1. **Insights summary**: read `~/workspace/guacamayo/.claude/docs/insights-summary.md` first
   (written by `/workflow-insights` — contains experiment verdicts, recommendations, model/skill/tool
   economics, and trends). If it doesn't exist or is stale (>7 days), fall back to running
   `python3 ~/.claude/scripts/insights.py --dry-run` for fresh mechanical stats, or read
   recent session JSONL under `~/.claude/projects/<project-slug>/`. Look for: repeated
   permission prompts for the same command shape, the same manual fix applied in multiple
   sessions, hook blocks that the user then overrode, tool errors retried verbatim.

   Read the `## Failure Attribution` section. Use category weights when triaging findings:
   - `env` errors → infrastructure/config findings, not code or spec findings
   - `tool` errors → hook or MCP config findings
   - `code` errors → skill/hook/workflow findings (note: retry-unknown — may include transients)
   - `unknown` → flag as a taxonomy gap (lookup table needs expansion)
   Never attribute an `env` error to a code or spec cause. Do not generate findings
   from `unknown` — surface the gap count instead.
2. **Growth-entry graduation**: `guacamayo/.sounding/growth.md` — entries tagged
   `[discovered]` that are *process* learnings (about workflow/tooling, not identity).
   These die in the accumulator unless promoted. Flag each as a graduation candidate with
   a proposed target (rule/skill/hook). Do NOT edit `.sounding/` — flag only; /reflect
   and /synthesize own that space.
3. **Hook fire patterns**: if hook logs exist, hooks that fire constantly (candidate for
   a fix upstream of the hook) or never (dead weight).
4. **Plan-doc drift**: recent docs in repo `.claude/docs/plans/` (one doc per work
   item, `YYYY-MM-DD-<slug>.md`) — compare Execution Notes / deviations against the original
   steps. Recurring deviation categories are tooling gaps.
5. **Skill coverage** — read the `## Skill Coverage` section of `insights-summary.md`
   (written by `/workflow-insights` step 7). Two opposite findings live here:
   - **Skill exists but is never invoked** → a *description* problem, not a value problem.
     The `Skill` tool matches on `description:` frontmatter, so a skill that never
     auto-triggers usually has a weak one. Propose a description rewrite
     (`skill-creator` has description-optimization), not deletion. Recommend deletion only
     where a skill is never invoked AND superseded by a named alternative.
   - **Skill is missing** — the inverse, and it has no live signal: "I should have had a
     skill for this" is only visible in retrospect. Look for the same multi-step work
     shape repeated across ≥3 sessions with **zero** skill invocations in those sessions.
     That cluster is the trigger to propose `skill-creator`. Name the recurring shape and
     cite the sessions; a vague "we do a lot of X" is not a finding.

   Also flag **typo'd invocations** (a `/name` with no skill on disk, e.g.
   `design-inistiative`) — these fail silently with no error, so they read as user error
   but are really a missing-feedback problem.

## Step 2 — Findings → proposals

Per finding, emit exactly this shape:

```markdown
### F<N>: <one-line friction statement>
- Tag: stop | keep | improve
- Friction observed: <what kept happening>
- Evidence: <session/file refs — at least one concrete pointer>
- Proposed diff: <actual diff or precise edit, ready to apply>
- Target: <file path>
- Enforcement level: hook | skill/protocol | CLAUDE.md/rules | MEMORY.md
- Metric: <type>:<signal> <threshold> (see ledger Experiment Tracking section for types)
```

**Tagging rules** (from `~/.claude/rules/agile.md`):
- **stop** — actively costing us; mechanical fix or delete → `ready` issue if scoped, `backlog` otherwise
- **keep** — verified working; no issue → ledger row graduates to `verified`
- **improve** — needs design/research before actionable → `backlog` issue or `inbox.md` line

**Write targets by enforcement strength** (decided, don't relitigate):
hooks > skills/protocols > CLAUDE.md/rules > MEMORY.md. Pick the strongest level that
fits the friction; if you propose a weaker one, say why (e.g. not mechanically checkable).

**Doc-writer boundary** (decided): machine-consumed docs (`.claude/`, CLAUDE.md, rules)
are this loop's native output. Human-consumed docs (READMEs, design docs, wiki) belong to
librarian's pipeline or humans — flag staleness, never propose direct edits to them.

## Step 3 — Eval gate for skill changes

Any proposal that modifies a skill ships with a **before/after eval sketch**: the
prompt(s) that exercise the behavior, what the current skill produces, what the changed
skill should produce, and how to judge it (skill-creator's eval harness where it fits).
No sketch → the proposal is marked `draft`, not ready for review.

## Step 4 — Output and ledger rows

Group findings by write target (all hook changes together, etc.), most-severe friction
first. End with:

1. **Proposed ledger rows** for every accepted-if-approved change, in ledger format with
   status `hypothesis`, a typed **Metric** (from the vocabulary: `absence:`, `count-drop:`,
   `presence:`, `ratio:` — see ledger header), and a concrete verification test.
2. **Ledger maintenance**: if the ledger exceeds ~1 screen, propose compressing verified
   rows into a one-line monthly rollup.

Through Step 4 nothing is written outside the retro report. Then stop and hand the report
to Ramsey for Step 5.

## Step 5 — Apply (gated on approval)

Present the grouped findings and ask Ramsey which to apply — by finding ID (`F1, F3`),
`all`, or `none`. **Apply nothing until this answer comes back.** Silence is not approval.

Skip any `draft` finding (Step 3 eval sketch missing) — say so; it is not eligible until
promoted out of draft. For each **approved** finding:

1. Apply its Proposed diff to its Target, verbatim as reviewed. If the target drifted since
   Step 2 and the diff no longer applies cleanly, do NOT improvise a new edit — report the
   mismatch and re-propose that one for a fresh look.
2. After a settings.json edit, validate it (`jq empty ~/.claude/settings.json`); after a
   hook edit, `chmod +x` and smoke-test it the way its sibling hooks are tested. A hook or
   settings change that fails validation is rolled back, not left half-applied.
3. Machine-consumed targets only (`.claude/` skills/hooks/settings, CLAUDE.md, rules) — the
   loop's native output. Never apply to human-consumed docs (READMEs, wiki) or to
   `.sounding/` identity files even if a finding names one; re-flag instead.

After applying, add the ledger rows (status `hypothesis`, with the verification test) for
every finding that landed. Report per finding: applied | skipped-draft | skipped-declined |
re-proposed (drift), with the file touched. Ramsey commits — this loop never commits or
pushes.

## Step 6 — Write findings to the board (after approval)

For each approved finding, write it to its destination based on the Tag:

### stop / improve → GitHub Issue
```bash
cd ~/workspace/guacamayo && gh issue create \
  --title "F<N>: <one-line friction>" \
  --label "<label>" \
  --body "<problem + evidence + metric>"
```

Label mapping:
- **stop** (scoped, mechanical) → `ready`
- **stop** (needs design) → `backlog`
- **improve** → `backlog`

Issue body format:
```markdown
## Problem
<Friction observed — one sentence>

## Evidence
<Session/file refs>

## Proposed fix
<Proposed diff from the finding, or "needs research">

## Metric
<type>:<signal> <threshold>

## Source
<date> /workflow-retro F<N>
```

### keep → ledger only
No issue. Graduate the ledger row: `hypothesis → verified (evidence)`.

### Unscoped ideas → inbox
If a finding is too vague for an issue (no clear problem statement), append one line to
`~/workspace/guacamayo/.claude/docs/state/inbox.md` instead of creating an issue.

Report the issue URLs created so Ramsey can verify.
