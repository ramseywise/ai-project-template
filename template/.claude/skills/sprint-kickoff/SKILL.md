---
name: sprint-kickoff
description: >
  Generate a first-week plan from DESIGN.md and evaluation targets. Identifies what to
  build first, what to validate, and concrete "done when" criteria. Use at the start of
  a new sprint or when the team asks "what should we work on first?" Triggers on:
  "sprint kickoff", "start the sprint", "what do we build first", "first week plan",
  "kickoff plan", "where do we start".
---

# sprint-kickoff

Turn a scoped design into a concrete first-week action plan. Answers: "We have a
DESIGN.md and milestones — what do we actually do on Day 1?"

## Before you start

Locate and read (fail if missing):
1. `DESIGN.md` — the scoped design document (from `/scope-poc`)
2. `.claude/docs/milestones/*.md` — active milestone(s) (from `/define-milestones`)

Optional but useful:
- `evals/targets.yaml` — evaluation targets if defined
- `.claude/docs/PROJECT-PROFILE.md` — for capacity constraints

## Process

### 1. Identify the critical path

From DESIGN.md and the current milestone, extract:
- The 2-3 tasks that unblock everything else (data model, core integration, key abstraction)
- The single riskiest unknown (the thing most likely to invalidate your plan)
- The first user-visible result (what can we demo soonest?)

### 2. Define validation-first ordering

Prioritize work that **proves or disproves assumptions** over work that builds features:

| Priority | Work type | Example |
|----------|-----------|---------|
| 1 | Risk spike | "Can we actually get transcripts from the Google Meet API?" |
| 2 | Core data path | "Ingest one real document, retrieve one answer" |
| 3 | Integration skeleton | "Slack message sends successfully from the app" |
| 4 | Feature build | "Action item extraction from transcript" |

### 3. Generate the plan

Write a plan with exactly these sections:

**Sprint goal** — one sentence describing what's true at end of week 1 that isn't true today.

**Day 1-2: Spike + scaffold**
- The risk spike task (timebox: 4 hours max, then decide go/no-go)
- Environment setup tasks (what each team member needs running locally)

**Day 3-5: Core path**
- The 2-3 tasks that establish the data path end-to-end (even if outputs are rough)
- First eval run (even if metrics are bad — establishes the baseline)

**Done-when checklist**
- [ ] Risk spike resolved: [specific question answered]
- [ ] Core data path works: [specific input → output demonstrated]
- [ ] Eval baseline established: [metric name] = [any number, even bad]
- [ ] Team can run locally: [command that proves it]

**Parking lot** — things explicitly NOT this week (reference from out-of-scope)

### 4. DSSG volunteer calibration

When the team is DSSG volunteers (signals: PROJECT-PROFILE mentions DSSG, cohort,
volunteer hours, semester timeline):

- **Assume 2-hour work blocks** — volunteers don't have 8-hour days; tasks must be
  completable in one sitting
- **Pair on Day 1** — first session should be synchronous (screen share) to unblock
  environment setup; async after that
- **Risk spike is the meeting agenda** — if the team only meets once in week 1, the
  spike result is the only must-have output
- **"Done when" must be runnable** — no "review the design" tasks; every item produces
  a concrete artifact or passing test

## Output

Write to `.claude/docs/sprint-plans/week-N.md`:

```markdown
# Sprint Plan — Week [N]
Date: [today]
Milestone: [active milestone name]

## Sprint goal
[one sentence]

## Day 1-2: Spike + scaffold
- [ ] [task with owner if known]
- [ ] [task]

## Day 3-5: Core path
- [ ] [task]
- [ ] [task]
- [ ] [task]

## Done-when
- [ ] [concrete, verifiable condition]
- [ ] [concrete, verifiable condition]
- [ ] [concrete, verifiable condition]
- [ ] [concrete, verifiable condition]

## Parking lot
- [deferred item + reason]
```

## Rules

- Never plan more than 5 days ahead — uncertainty compounds; re-plan weekly
- Every task must have a verb and a noun ("set up Postgres locally", not "database")
- The risk spike gets a timebox — if it's not resolved in 4 hours, escalate or pivot
- "Done when" items are binary (yes/no) — no "mostly done" or "80% complete"
- If DESIGN.md has no evaluation targets, the first sprint MUST include "define what good looks like"

---

**Upstream:** `/define-milestones` (what are we building toward), `/scope-initiative` (task breakdown)
**Next:** `/execute-plan` or `/execute-tasks` to begin implementation
