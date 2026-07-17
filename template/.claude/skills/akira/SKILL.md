---
name: akira
description: Proactive codebase quality checks. Three modes — kiyoko (yin wanderer, mid-session questions about the recent delta), kaneda (yang scanner, spawns the vendored akira-scan agent, writes a findings doc), dao (the path, triage per finding: auto-fix low-blast-radius changes, surface complex ones for review, discard false positives). Trigger on "akira", "quality check", "what did we miss", or any code quality request.
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, Agent
---

# /akira

Runs entirely through Claude Code — no product source involved. The scan mode
delegates to the vendored `akira-scan` agent (`.claude/agents/akira-scan.md`);
kiyoko and dao run in-session.

## Parse arguments

- `wander`, `kiyoko`, `?` → kiyoko mode
- no args, `scan`, `kaneda` → kaneda mode
- `dao`, `fix` → dao mode
- path glob (e.g. `src/agents/<slug>/`) → kaneda mode scoped to those files

## kiyoko (yin — wander and ask)

Read the recent delta (`git diff HEAD~5 --stat`, then the interesting hunks) and
the files it touches. Ask 2–4 pointed questions in chat about what looks
underspecified, untested, or inconsistent — questions, not findings. Do not
edit anything.

## kaneda (yang — scan)

1. Collect the target files: the argument glob if given, else the project's own
   source (`git ls-files` filtered to source dirs — respect the Makefile's
   `LINT_PATHS` scope; skip vendored `.claude/`/`.agents/` reference material).
2. Spawn the `akira-scan` agent with the file list (batch into 2–3 agents in
   parallel if the list is large). It reports ranked findings; it never edits.
3. Write the merged, deduplicated findings to
   `.claude/akira/findings/findings-{YYYY-MM-DD}.md` (gitignored), ranked
   most-severe first, each as `file:line — issue — severity`.
4. Summarize the top findings in chat and point at the doc; suggest `/akira dao`.

## dao (the path — triage and fix)

1. Read the newest `.claude/akira/findings/findings-*.md`.
2. Per finding, triage: **auto-fix** (low blast radius, mechanical), **surface**
   (real but needs a human decision — leave in the doc with a note), or
   **discard** (false positive — note why).
3. Apply auto-fixes, then run `make test` (and `make lint-check`). Revert any
   fix that breaks them (`git checkout -- <file>`).
4. Write a run summary at the top of the findings doc: fixed / surfaced /
   discarded counts and the test outcome. Never commit — leave staging to the
   user.
