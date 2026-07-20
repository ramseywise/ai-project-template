---
name: design-initiative
description: "Take a named initiative and produce a Linear-ready technical backlog: failure modes, HMWs, research section, task backlog with acceptance criteria and t-shirt sizes, dependency mapping, and Linear hierarchy. Use when an initiative is named and agreed on. Aliases: /initiative, /design-inistiative."
disable-model-invocation: true
allowed-tools: Read Bash Grep Glob WebSearch Write
---

## Target repo

Same convention as the phase protocols (research/plan/execute/code-review): a
`repo:<name-or-path>` token in `$ARGUMENTS` targets another workspace repo (bare name
resolves to `~/workspace/<name>`); all repo-relative paths and git/test commands resolve
against it, and artifacts land in the TARGET repo. No token → the cwd's repo; in a
meta/workspace-root session, ask rather than defaulting.

Scope the following initiative into a Linear-ready backlog: `$ARGUMENTS`

## Inputs (ask if not provided)

1. **Initiative name + one-line goal**
2. **Known failure modes** — 3-5 distinct ways the system currently fails (patterns, not symptoms)
3. **Brief or requirements doc**
4. **Existing assets** — prototypes, research, analogous systems
5. **Team roles available**
6. **MVP scope** — in vs out
7. **Milestones** — the initiative's checkpoint list from `/define-milestones`
   (`.claude/docs/milestones/<initiative-slug>.md`); if missing, run that first

## Sections

1. **Failure modes & HMWs** — table: # | Failure mode (`root cause -> symptom`) | Pain point | HMW. Every subsequent task traces to at least one failure mode.
2. **Research** — existing assets (reuse/adapt/reference), libraries per layer, technical unknowns (what each blocks), roadblocks + dependencies table.
3. **Task backlog** — initiative goal + MVP definition of done. Per task: goal, deliverable (concrete, not "implement X"), key work bullets, risks/questions, size (S/M/L/XL).
4. **Summary table + critical path** — # | Task | Failure mode | Size | Key dep | Owner | MVP? Plus: week-1 decisions, highest-risk dependency, tasks that must be designed together.
5. **Open questions** — numbered, each names who must answer. Categories: data access, infra, product, ownership, policy, phasing.
6. **Linear hierarchy** — Initiative → Project → Milestone → Issues (tasks): every task attaches to one of the initiative's milestones (from `/define-milestones`), with acceptance criteria (Given/When/Then + metric + integration criterion) and blocking relationships. A task that fits no milestone means either the backlog has scope creep or the milestone list is missing a checkpoint — resolve, don't orphan.

## Task constraints

- Every deliverable is concrete (running system, document, dataset) — not "implement X"
- Every task traces to at least one failure mode
- T-shirt sizes: S (<1wk, few unknowns), M (1-2wk, some unknowns), L (2-4wk, significant unknowns), XL (>sprint, major decisions)
- Day-one decisions (embedding model, schema, vector store) appear first in critical path

---

**Upstream**: `/design-sprint` if still ideating what to build — run that first to get named initiatives and workstream clusters. `/define-milestones <initiative>` for the checkpoint list this backlog attaches to.

**Next step**: `/doc-to-linear-tickets` to push the task backlog (Section 6 Linear hierarchy) into actual Linear issues once the scope is reviewed and agreed.
