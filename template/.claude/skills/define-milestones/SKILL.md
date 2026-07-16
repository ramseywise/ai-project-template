---
name: define-milestones
description: >
  Define the milestones inside a named initiative — the phase-level goalposts that break an
  initiative into verifiable checkpoints before task planning. Follows Linear's hierarchy:
  Initiative → Project → Milestone → Issue. Use when an initiative is agreed and needs its
  "done looks like" checkpoints. Triggers on: "define milestones", "break down this initiative",
  "what are the phases", "milestone plan for X", "what ships first in X", "release planning".
---

# define-milestones

Break one initiative into milestones. A milestone is a checkpoint *inside* an initiative — a
verifiable state of the system, not a bundle of work. Hierarchy (matches Linear):
**Initiative → Project → Milestone → Issue.** This skill takes one named initiative and produces
its milestones; task breakdown per milestone happens in `/scope-initiative`.

## Before you start

Ask if not provided (or derive from named planning docs):

1. **Initiative name + one-line goal** — if the initiative isn't agreed yet, run `/design-sprint` first
2. **Existing phase structure** — most plans already have phases/sprints; milestones formalize
   their boundaries, they don't invent new ones
3. **Hard constraints** — decision gates, external deadlines, capacity
4. **Dependencies on other initiatives** — what must exist elsewhere before each checkpoint is reachable

## Process

1. **Initiative goal statement** — one sentence: what does this initiative deliver and for whom?
2. **Milestones (2–6)** — each is a named system state, ordered. Per milestone:
   - **Done-condition** — a verifiable observation ("a service key returns real rows from
     `GET /kb/search`"), never activity ("API built")
   - **Gates** — decisions or external dependencies that block it, marked ⛔
   - **Target** — date or sequence position; only pin dates driven by real external events
3. **Cross-initiative dependencies** — which milestones here unblock or wait on milestones in
   other initiatives
4. **Out of scope** — what this initiative explicitly does not cover, with reasons

## Output

Write one file per initiative to `.claude/docs/milestones/<initiative-slug>.md`:

```markdown
# Initiative: <name>
Date: <today>
Goal: <one sentence>
Source plan: <path to the plan/roadmap section this formalizes>

## Milestones

### M1 — <named system state>
- **Done when:** <verifiable condition>
- **Gates:** <⛔ decision/dependency, or "none">
- **Target:** <date if externally driven, else "after M0" / "sequence only">

### M2 — ...

## Cross-initiative dependencies
- <this M unblocks / waits on <initiative>:<milestone>>

## Out of scope
- <item with reason>
```

If several initiatives are being planned in one cycle, also maintain
`.claude/docs/milestones/sequencing.md` — a one-page cross-initiative timeline (target dates,
critical path, decision gates). Sequencing targets live there, not as milestone entities.

Then, if the repo uses Linear: create each milestone as a **project milestone** under the
initiative's Linear project (done-condition in the description). Skip for repos without Linear.

## Rules

- A milestone is a state, not a workstream — if it names ongoing activity, it's an initiative
  or a project, not a milestone
- One verifiable done-condition per milestone — if you need two unrelated ones, split it
- Milestones inherit the source plan's phase boundaries unless there's a stated reason to re-cut
- Only externally-driven milestones get calendar dates; the rest get sequence positions —
  fake dates on gated work hide the real critical path (the gate)
- Defer rather than stretch — fewer verifiable milestones beat many vague ones

## Semester/cohort-aligned patterns (DSSG / volunteer teams)

When the driving event is a semester or cohort cycle (signals: user mentions DSSG,
cohort, demo day, volunteer rotation, hackathon), apply these milestone patterns:

| Sprint block | Weeks | Milestone focus | Done when |
|-------------|-------|-----------------|-----------|
| **Foundation** (sprints 1-2) | Weeks 1-4 | Scaffold, core data model, first integration working | `make test` passes; one real data source ingested; team can run the system locally |
| **Core value** (sprints 3-4) | Weeks 5-8 | The demo-day deliverable — the thing that makes the nonprofit say "yes" | Demo scenario works end-to-end; eval metrics meet targets; stakeholder has seen it |
| **Handoff** (sprints 5-6) | Weeks 9-12 | Documentation, operator training, sustainability plan | Next cohort can run/modify without original team; README + runbook + known-issues complete |

**Key constraints for cohort milestones:**
- **Demo day is non-negotiable** — treat it as a hard external deadline, not a soft target
- **Handoff milestone is mandatory** — DSSG volunteers rotate; a project with no handoff docs dies when the cohort ends
- **Each milestone maps to ~2 volunteer sprints (4 weeks)** — don't plan 6 milestones for a 12-week cohort; 3 is the maximum
- **"Core value" milestone is the only one the nonprofit sees** — Foundation is internal; Handoff is for the next team. Core value is the product.

If the cohort is shorter (e.g., a 4-week hackathon sprint), compress to 2 milestones:
Foundation (week 1) + Core Value (weeks 2-4). Skip Handoff — hackathon output is a prototype, not a maintained system.

---

**Upstream**: `/design-sprint` if the initiative list itself isn't agreed yet.
`/project-discovery` if a Project Profile exists — read capacity constraints for timeline.
**Next**: `/scope-initiative <initiative-name>` to break each milestone into a task backlog
with acceptance criteria; tasks attach to the milestones defined here.
