---
name: workflow-review
description: "Phase 4 review — plan fidelity + multi-reporter code review + DoD assessment + merge verdict. Use after execution completes, or to review an open PR. Triggers: 'review PR #42', '/workflow-review', '/workflow-review my-feature', 'check the PR', 'review the diff', 'code-pr 42'."
skills: [review-shared]
allowed-tools: Read Grep Glob Bash Agent
---

Review implementation against plan (if one exists) AND review code quality via
multi-reporter orchestration. This is the unified post-execution / post-PR review.

`$ARGUMENTS` — one of:
- A PR number or URL (`42`, `#42`, `https://...`) → PR review mode
- A work-item slug (`my-feature`) → plan-doc review mode
- Empty → discover: check for `Status: IN PROGRESS` plan doc, else `gh pr list`

## Target repo

All paths resolve against a **target repo**:

1. A `repo:<name-or-path>` token anywhere in `$ARGUMENTS` (strip before routing)
   — bare name resolves to `~/workspace/<name>`.
2. Otherwise, the repo containing the cwd.
3. In a meta/workspace-root session with no `repo:` token, ask which repo.

Run commands with the target as working dir. Artifacts land in the TARGET repo's
`.claude/docs/plans/` so that repo's own sessions find them.

---

## Stage 1: Context Brief

Produce a context brief (per `review-shared/references/context-brief.md`). Gather:

1. **PR metadata** (if PR mode): `gh pr view <number> --json title,body,headRefName,baseRefName,labels,reviewRequests`
2. **Diff**: `gh pr diff <number>` (PR mode) or `git diff main...HEAD` (plan mode)
3. **Changed files**: from PR or git diff
4. **Repo context**: read CLAUDE.md, check for SANYI.md, check for Refs: line
5. **CI status** (PR mode): `gh pr checks <number>`
6. **Callers of changed symbols**: Grep for function/class names from the diff
7. **Review profile**: infer `general` or `agent-system` from imports and file paths.
   Agent-system if any changed file imports LLM/agent frameworks or lives under `agents/`,
   `*_agent/`, `prompts/`.
8. **Plan doc** (if exists): find matching `.claude/docs/plans/*.md` by slug or branch name.
   If found, read `## Plan` section for fidelity check.

Fill the context brief template. Unknown fields = "unknown", not guessed.

## Stage 2: Plan Fidelity (conditional — skip if no plan doc)

For each plan step:

| Plan said | Code shows | Tests | Status |
|-----------|-----------|-------|--------|
| Step 1: ... | [actual] | PASS/FAIL | Match / Deviation / Missing |

### Stub detection

Check key files for: `TODO`, `NotImplementedError`, `return None`, `pass` on critical
paths. Blocker if on critical path, warning otherwise.

Deviations become findings with `merge_impact: important` (justified deviation) or
`blocker` (unjustified omission).

## Stage 3: Dispatch Reporters

Run these in parallel where possible:

### akira-scan (quality)
Split changed files into batches of ~5. Spawn `akira-scan` agent on each batch
(model: haiku, pass context brief summary + file paths). Agent outputs canonical schema
with evidence tags (see `~/.claude/refs/finding-schema.md`).

### SANYI (contracts)
If SANYI.md exists at repo root: run `/sanyi review` protocol on the diff.
Map severities: BY-* → **[Blocking]**, JY-* → **[Non-blocking]**, BN-1/notices → **[Nit]**.
Report-only — never auto-fix a contract violation inside a review.
If no SANYI.md: skip, note in dispatch summary.

### Lint and tests
Run `make lint` / `make test` if available; fallback to stack-specific commands
(`uv run pytest --tb=short -q`, `npx tsc --noEmit`, etc.).
Record pass/fail. Test failures become findings with `merge_impact: blocker`.

### Dimension coverage
For agent-system PRs: akira-scan already checks conditional dimensions 6-7 from
`review-dimensions.md`. No separate dispatch needed.

## Stage 4: Merge and Deduplicate

Collect all findings (plan fidelity + reporters) in canonical schema format. Apply
merge logic from `review-shared`:

1. **Group** findings by file+lines overlap (within 5 lines) AND category similarity
2. **Judge** if grouped findings describe the same underlying issue
3. **Merge** confirmed duplicates: preserve all source IDs, use most precise root cause,
   take higher merge_impact, take more certain evidence_state
4. **Rank** merged findings: blockers first, then important, questions, suggestions, nits

## Stage 5: DoD Assessment

Assess each item from `~/.claude/refs/review-dod.md` as met / gap / n/a.
Gaps become findings with appropriate merge_impact. Repo-specific DoD overrides defaults.

If a plan doc exists, also check:
- All plan steps accounted for (from Stage 2)
- Status line present and correct
- Acceptance criteria from the plan/issue met

## Stage 6: Judge — Merge Verdict

Apply verdict rules from `review-shared/references/review-report.md`:

- Any `merge_impact: blocker` → **request_changes**
- Only important + suggestion + nit → **comment**
- No findings or only nits → **approve**
- Reporter failures that could mask blockers → **insufficient_context**
- Questions alone (no blockers) → **comment**

## Stage 7: Report

Produce the unified report:

```markdown
# Review — #<number> <title> (or <slug>)

## 1. Overall Understanding
[1-3 sentences]

## 2. Review Contract
[From context brief]

## 3. Plan Fidelity
[Plan step table — only if plan doc exists. Otherwise: "No plan doc — standalone review."]

## 4. What Looks Strong
[Genuine positives, not filler]

## 5. Blocking Findings
[merge_impact: blocker findings with canonical IDs]

## 6. Important Findings
[merge_impact: important]

## 7. Questions and Hypotheses
[merge_impact: question + hypothesis-state findings]

## 8. Suggestions and Nits
[merge_impact: suggestion | nit]

## 9. Testing and Evaluation Assessment
[Coverage, gaps, repeated-run consideration for agent code]

## 10. Definition of Done Assessment
[DoD checklist table: item | status | note]

## 11. Reporter Dispatch Summary
| Reporter | Status | Findings |
|----------|--------|----------|
| plan-fidelity | ran/skipped | N findings |
| akira-scan | dispatched/skipped | N findings |
| SANYI | dispatched/skipped | N findings |
| lint/tests | ran/skipped | pass/fail |

## 12. Merge Verdict
**approve** | **comment** | **request_changes** | **insufficient_context**
[1-2 sentence rationale]
```

If plan doc exists, append the review section to the plan doc and set `Status: EXECUTED`
on approval.

## Stage 8: Action (read-only default)

Report the verdict to the user. Do NOT run `gh pr review` unless explicitly authorized.

> "Verdict: **[verdict]**. Want me to submit this as a GH review?"

If authorized:
- `approve` → `gh pr review <number> --approve -b "<summary>"`
- `request_changes` → `gh pr review <number> --request-changes -b "<summary>"`
- `comment` → `gh pr review <number> --comment -b "<summary>"`

For plan-doc mode (no PR): append `## Review` section to plan doc, update Status.

## Boundaries

- Never commit, push, or merge — Ramsey commits.
- Never auto-fix findings — report only. Recommend `/akira dao` for safe fixes.
- Read-only by default; GH review submission requires explicit authorization.
- Per-reporter failures are reported (not retried infinitely), noted in dispatch summary.
- Max 3 review rounds — if issues persist, escalate to user.
