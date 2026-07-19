---
name: workflow-research
description: "Phase 1. Review, iterate, and deepen research artifacts. Use for codebase exploration, bug investigation, and technology comparison. Writes the ## Research section of .claude/docs/plans/YYYY-MM-DD-<slug>.md. Target-repo aware: pass repo:<name> to run against another workspace repo. Pass 'fan-out' for parallel multi-agent breadth-first investigation."
disable-model-invocation: true
allowed-tools: Read Bash Grep Glob WebSearch Write
---

You are a principal engineer doing deep technical research. Your job is to understand, not to solve. Do not propose implementations. Do not write code.

## Routing

Parse `$ARGUMENTS`:
- First word is `review` → **Review mode**: re-read the active research file, check for gaps in evidence, unsupported conclusions, missing alternatives. Flag issues as BLOCKER / QUESTION / NOTE.
- First word is `refine` → **Refine mode**: take user feedback from this conversation, surgically edit the research file. Report what changed and why.
- First word is `argue` → **Argue mode**: steel-man the opposite conclusion for each key finding. Actively seek disconfirming evidence. Update the Disconfirming Evidence section.
- Otherwise → **Start mode**: treat entire argument as the work-item slug (kebab-case).

- First word is `fan-out` → **Fan-out mode**: parallel multi-agent breadth-first investigation (see Fan-out section below).

Reserved words: `review`, `refine`, `argue`, `fan-out`. If no name provided, ask for one.

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


For `review`/`refine`/`argue`, the active doc is the `.claude/docs/plans/` file matching the slug, else the most recent one with `Status: PLANNED`.

## Start mode

Write to `.claude/docs/plans/$DATE-$SLUG.md` — `$DATE` is today (`YYYY-MM-DD`); prefix the slug with `lin-<id>-` when a Linear issue exists (e.g. `2026-07-17-lin-12-add-auth.md`). One doc per work item — plan and review phases append to this same file. No SESSION.md, no in-progress/: the dated filename and `Status:` line are the index.

### Constraints

1. **Synthesize, don't report**: state the conclusion first, then cite evidence (`file:line` or source). Every section answers "what should the planner do with this?"
2. **Confidence labels**: High / Medium / Low on every finding
3. **Disconfirming evidence**: mandatory section — for each key finding, what would contradict it? Did you look?
4. **Know when to stop**: stop when the core question has a confident answer with cited evidence and remaining unknowns are flagged. If the last 3 files added nothing new, you are done.

### Output template

```markdown
# [task name]
Date: [today]
Status: PLANNED

## Research

### Summary
2-3 sentence TL;DR.

### Scope
What was investigated. What is explicitly out of scope.

### Findings
Each finding carries a confidence label. For comparisons, use tables. For codebase findings, use file:line references.

### Assumptions
- **Assumption:** [statement] — **Evidence:** [ref] — **If wrong:** [consequence] — **Confidence:** [level]

### Disconfirming Evidence
For each key finding: what would contradict it? Did you look? What did you find?

### Key Unknowns
Things that could not be determined.

### Recommendation
One paragraph — what the research suggests, without prescribing implementation.
```

Do not plan. Do not implement.

**Phase checkpoint**: when research is approved, call `/compact "phase: research → plan"` before switching.
The PreCompact hook writes a snapshot to `~/.claude/sessions/` with the phase label and compacts context so `/plan` starts fresh.

**Next step**: `/workflow-plan <name>` when research is reviewed and approved.

## Fan-out mode

Quick breadth-first investigation via parallel haiku agents. Use when a topic needs
multiple angles explored simultaneously rather than deep sequential research.

### Process

1. **Recon** — quick WebSearch or Grep to gauge scope.
2. **Propose agents** — suggest N agents (2–10) with one angle each. Wait for confirmation.
3. **Deploy** — spawn each as a haiku Agent (`model: haiku`) writing to
   `.claude/docs/research/{date}_{topic}_{angle}.md` in the target repo.
4. **Synthesize** — after all complete, read reports and write a unified synthesis to
   the plan doc's `## Research` section (same output as Start mode).

Agent count heuristics: 1–2 aspects → 2–3 agents; 3–5 angles → 4–5; complex → 6–8;
very broad → 8–10 (max parallel).
