---
name: design-sprint
description: "Run a full design sprint for any use case — deconstruct problems and pain points, generate HMW statements, define technical solutions, cluster into workstreams, map dependencies, and produce an initiative backlog. Use when starting a new product, feature, or platform initiative from scratch."
disable-model-invocation: true
allowed-tools: Read Bash Grep Glob WebSearch Write
---

Run a full design sprint using IDEO / Stanford d.school HMW methodology for: `$ARGUMENTS`

## Inputs (ask if not provided)

1. **Use case** — product, feature, or problem space
2. **Known constraints** — market, language, tech stack, team roles
3. **Existing data** — research, ticket data, prototypes, production metrics
4. **Scope boundary** — what is explicitly out of scope

## Phases

1. **Deconstruct** — problems, pain points, insights, opportunities. Table: Area | Finding | Implication.
2. **HMW statements** — reframe each finding as a How Might We question. Outcome-oriented, not solution-prescribing.
3. **Technical solutions** — for each HMW: what's required + concrete named technical approach.
4. **Workstream clustering** — group by WHO (FE), WHERE-BE, WHERE-AI, WHERE-data, WHY (observability), WHERE-Ops. Note cross-cluster items.
5. **Initiative definition** — 5-7 named initiatives. Each: name, one-sentence goal, components, roles, cross-initiative dependencies. First initiative has zero external deps.
6. **Dependency mapping** — HTML artifact per initiative: cards with title, description, needs, enables, role badge. Color-coded by role.

## Lightweight mode (`--lightweight`)

When invoked with `--lightweight` or when capacity is clearly "weekend sprint" or
the team is 1-2 people, compress to 3 phases:

1. **Deconstruct** — same as full mode (problems, findings table)
2. **HMW statements** — same (reframe findings)
3. **2-3 Initiatives** — skip workstream clustering and dependency mapping. Name
   2-3 initiatives directly from the HMWs, each with: name, one-sentence goal,
   key components. First initiative has zero external deps.

Skip Phases 4-6 (workstream clustering, 5-7 initiative expansion, HTML dependency
artifacts). The team doesn't need dependency cards when there are only 2-3 things
to build and everyone fits in one room.

**Use lightweight when:** Project Profile shows "weekend sprint" or team ≤ 3 people;
or user explicitly asks for a quick version.

## DSSG volunteer context

When running for a DSSG project (signals: user mentions DSSG, nonprofit, cohort,
volunteer team), seed the Deconstruct phase with these common nonprofit pain points
as prompts (not assumptions — ask if they apply):

- Data trapped in spreadsheets / Google Sheets with no API access
- Manual report compilation from multiple disconnected sources
- Repetitive constituent lookup across fragmented case management tools
- Handoff friction between rotating volunteer cohorts (knowledge loss)
- No systematic way to measure program outcomes (anecdotal only)

These are starting points for the Deconstruct table, not conclusions. If the user's
actual pain points are different, follow those instead.

## Quality constraints

- Be specific to the use case — no generic outputs that could apply to anything
- Use real numbers, benchmarks, and named tools where they exist
- Cite analogous systems or prior art
- If multilingual requirements exist, call them out as day-one decisions

---

**Upstream:** `/project-discovery` if a Project Profile exists — read it for pain points
and constraints before starting the Deconstruct phase.

**Next step**: `/scope-initiative <initiative-name>` for each named initiative once the workstream list is agreed. `design-sprint` answers *what* to build; `scope-initiative` answers *how* — failure modes, backward mapping, task backlog, Linear hierarchy.
