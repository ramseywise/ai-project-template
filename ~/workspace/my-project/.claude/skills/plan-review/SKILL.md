---
name: plan-review
description: "Phase 2. Review, iterate, and refine implementation plans. Reads the ## Research section of the active doc in .claude/docs/plans/ and appends the ## Plan section to it."
disable-model-invocation: true
allowed-tools: Read Grep Glob Bash Write
---

You are a principal engineer writing an implementation plan. Do not write production code. Do not implement anything.

## Routing

Parse `$ARGUMENTS`:
- First word is `review` → **Review mode**: check the active plan against its research for alignment, completeness, and sequencing. Output a verdict (see below).
- First word is `refine` → **Refine mode**: take user feedback, surgically edit the plan file. If change affects >2 steps, summarize ripple effects and confirm first. Report what changed.
- Otherwise → **Start mode**: treat entire argument as the work-item slug (kebab-case).

Reserved words: `review`, `refine`. If no name provided, ask for one.

The active doc is the `.claude/docs/plans/` file matching the slug, else the most recent one with `Status: PLANNED`.

## Start mode

1. Read the active doc's `## Research` section. If no doc exists, create one: `.claude/docs/plans/$DATE-$SLUG.md` (`YYYY-MM-DD`; prefix slug with the issue id when a tracker issue exists) with a `Status: PLANNED` line. If task is small/understood/low-risk/familiar, proceed without research.
2. Run `git status` and `uv run pytest --tb=no -q` for baseline.
3. Read every file that will be touched before specifying changes.

Append `## Plan` to the active doc. No SESSION.md — the dated filename and `Status:` line are the index.

### Key constraints

- **Scope first**: write Out of Scope section BEFORE any steps
- **Step completeness**: every step has exact files (+line ranges), what to change, a code snippet (before/after), a runnable test command, and a "done when" condition
- **Step sizing**: each step fits within 40% of a context window
- **Split large plans**: >8 steps → split into phases with review boundaries
- If you cannot be specific about a file or line, flag it as a blocker — do not guess

### Output template

```markdown
## Plan
Date: [today]
Based on: [## Research above or "direct codebase inspection"]

### Goal
One sentence.

### Approach
One paragraph — chosen approach and key tradeoff.

### Out of Scope
Explicit list.

### Steps
#### Step N: [name]
**Files**: `src/path.py` (lines X-Y)
**What**: Plain-language description.
**Snippet**: before/after pattern.
**Test**: `uv run pytest tests/test_file.py::test_name -v`
**Done when**: [verifiable condition]

### Test Plan
### Risks & Rollback
### Open Questions
```

## Review mode

Check the active doc's `## Plan` against its `## Research`:
1. **Alignment**: every step has basis in research; research warnings reflected in plan
2. **Completeness**: every step has files, test command, done-when condition
3. **Sequencing**: no step assumes something a later step creates
4. **Scope creep**: no implied requirements missing as steps
5. **Reuse**: no components rebuilt that already exist

Output: `Verdict: [ ] Execute-ready | [ ] Needs iteration — [N] blockers`
Flag issues as **BLOCKER** / **QUESTION** / **NOTE**.

If execute-ready: call `/compact "phase: plan → execute"` to snapshot and compact before implementing.
The PreCompact hook writes a checkpoint to `~/.claude/sessions/` so the execute phase starts with clean context.

**Next step**: `/plan-review review` to verify, then `/execute-plan` to implement.
