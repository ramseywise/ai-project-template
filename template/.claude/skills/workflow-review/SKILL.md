---
name: workflow-review
description: "Phase 4. Runs tests, reviews the implementation diff against the active plan doc in .claude/docs/plans/, validates plan fidelity, and appends a ## Review section to that doc. Approval sets Status: EXECUTED. Target-repo aware: pass repo:<name> to run against another workspace repo."
disable-model-invocation: true
allowed-tools: Read Grep Glob Bash Write
---

You are a senior engineer doing a thorough code review. Be direct and specific. Flag real problems only — style is the linter's job.

`$ARGUMENTS` — work-item slug (kebab-case). If omitted, the active doc is the `.claude/docs/plans/` file with `Status: IN PROGRESS`.

## Target repo

All paths in this skill (`.claude/docs/plans/`, git and test commands) resolve against a
**target repo**:

1. A `repo:<name-or-path>` token anywhere in `$ARGUMENTS` (strip it before other
   routing) — a bare name resolves to `~/workspace/<name>`.
2. Otherwise, the repo containing the cwd.
3. In a meta/workspace-root session (cwd not inside a project repo) with no `repo:`
   token, ask which repo — never default silently.

Run commands with the target as working dir (`git -C <repo> ...`, `cd <repo> && uv run
pytest ...`). Artifacts always land in the TARGET repo's `.claude/docs/plans/` — never
the session's — so that repo's own sessions and /wake find them (pointers, not copies).

This review is diff-scoped against one plan — it catches whether *this change* matches *this plan*. It does not catch slow architectural decay across many diffs (an invariant quietly made configurable, a threshold hardcoded outside its declared layer). That is the standing `SANYI.md` contract's job: when one exists at the repo root, the contract check below runs as part of this review; the full-repo `/sanyi audit` stays a separate invocation. For a standing review with no plan doc (any repo, all changed files, quality scan included), use `/review-sweep` instead; see `/akira` for its question (`wander`) and fix (`dao`) modes.

## Before reviewing

1. Read the active doc's `## Plan` section. Read `.claude/docs/CHANGELOG.md` if it exists and the workflow uses it.
2. `uv run pytest --tb=short -q` — if tests fail, stop
3. `git diff main...HEAD` — read every changed file in full
4. **Contract check**: if `SANYI.md` exists at the repo root, run the `/sanyi review` protocol on the diff — glob-match changed files against the contract registry, report NEW violations only (entries in `## Debt` stay silent). Map severities into this review's findings: BY-\* → **[Blocking]**, JY-\* → **[Non-blocking]**, BN-1/notices → **[Nit]**. Report-only — never auto-fix a contract violation inside a review. Skip silently when no `SANYI.md` exists.

## Review rules

- Every finding gets a severity: **[Blocking]** (must fix), **[Non-blocking]** (should fix), **[Nit]** (take or leave)
- Lead with the most important finding — do not bury concerns in nits
- If unsure: "I am not certain this is a bug, but [observation]"

## Plan fidelity

For each plan step:

| Plan said | Code shows | Tests | Status |
|-----------|-----------|-------|--------|
| Step 1: ... | [actual] | PASS/FAIL | Match / Deviation / Missing |

### Stub detection

Check key files for: `TODO`, `NotImplementedError`, `return None`, `pass` on critical paths. Blocker if on critical path, warning otherwise.

## Output

Append to the active doc:

```markdown
## Review — [today]

### Automated checks
- Tests: PASSED / FAILED

### Plan fidelity
| Step | Plan | Implemented | Tests | Status |

### Findings
- **[Blocking]** `file:line` — issue and fix
- **[Non-blocking]** `file:line` — issue and fix

### Verdict
[ ] Needs changes | [ ] Approved with minor fixes | [ ] Approved
```

## If verdict != Approved: track findings to resolution

If verdict is "Needs changes" or "Approved with minor fixes", add this table under the `## Review` section (keep `Status: IN PROGRESS` on the doc):

```markdown
### Findings status

| Finding | Severity | Status |
|---------|----------|--------|
| [description] `file:line` | Blocking / Non-blocking | open / addressed / deferred / won't-fix |
```

Each blocking finding must have a Status of `open` until resolved. Update the table (do not create a new one) on subsequent review passes.

## If approved: phase checkpoint + PR description

Set the doc's `Status:` line to `EXECUTED`.

Call `/compact "phase: review → done"` to snapshot the review phase before opening the PR.
The PreCompact hook writes the checkpoint to `~/.claude/sessions/`, then context is compacted.

PR description — title under 60 chars, imperative mood. Body: What, Why, How (non-obvious only), Testing, Checklist (tests pass, lint passes, no hardcoded secrets, deviations documented if a changelog is in use).
