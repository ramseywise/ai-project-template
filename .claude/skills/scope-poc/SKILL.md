---
name: scope-poc
description: >
  System design interview for a new AI project — produces DESIGN.md capturing problem,
  actors, MVP scope, and key decisions before handing off to /project-genesis.
  Triggers on: "scope a project", "design interview", "what should we build", "system design",
  "help me scope", "POC planning", "before genesis", "/scope-poc". Also triggered automatically
  when a user seems to be starting from scratch without a clear design.
  DSSG-aware: recognizes nonprofit-success-ai (customer portal) and project-mgmt-ai (lifecycle
  backend) and applies DSSG platform context automatically.
---

# /scope-poc

Upstream design conversation that runs **before** `/project-genesis`. Produces `DESIGN.md`.
The two skills in sequence: `/scope-poc` → `/project-genesis` → `copier`.

`/project-genesis` answers HOW to build it (infrastructure). This skill answers WHAT to build.
Don't conflate them — many design sessions happen weeks before the scaffold is run.

## Usage

```
/scope-poc [--output path/to/DESIGN.md]
```

| Arg | Default | Description |
|-----|---------|-------------|
| `--output` | `.claude/docs/DESIGN.md` (pre-scaffold) or `DESIGN.md` (in-project) | Where to write the design artifact |

---

## Steps

### Step 0 — DSSG detection

Before starting the interview, check if the project is a known DSSG platform project.
Signals: the user mentions "DSSG", "nonprofit-success-ai", "project-mgmt-ai", "dssg/",
"customer portal", "hackathon coordination", or the engagement lifecycle stages.

If DSSG platform is detected:
- Skip generic auth/data questions — Supabase Postgres is already the declared stack
- Load the shared context block below (§DSSG context) before starting the interview
- Ask only what's specific to THIS project's slice (stage ownership, actor, AI scope, MVP)
- Acknowledge what's already decided rather than re-deciding it

### Step 1 — Tier 1: Problem and actors

Have a real conversation (not a rigid checklist read aloud). Cover:

1. **What problem are you solving?**
   - What does someone do today without this system?
   - What does success look like — what would a demo show someone in 5 minutes?

2. **Who are the actors?**
   - Who uses this directly (humans)?
   - What other systems does it interact with?
   - Is there a distinction between internal users (staff/volunteers) and external users (clients)?

3. **What does the AI specifically do?**
   - Is this retrieval (find and surface relevant info), generation (draft/summarize), automation
     (take actions on behalf of a user), or orchestration (coordinate multiple steps)?
   - What does the actor do TODAY for this task, that the AI would do instead or augment?

Skip a question if the answer is obvious from context already given. This is a conversation,
not a form. If they've already said "it's a client portal for nonprofits to track their
engagement status," you know the actor without asking.

### Step 2 — Tier 2: System boundaries

4. **What existing systems does this connect to?**
   - Auth (existing identity provider, or building new?)
   - Data sources (existing DB, documents, APIs)
   - Destinations (where does AI output go — DB write, email, Slack, another system?)
   - If the Actors table (Step 1) has an **external, non-DSSG-staff** row and this project needs its own
     backend (not just retrieval) — name FOIA-Fluent's split-service shape (Next.js on Vercel + FastAPI on
     Railway, Supabase JWT shared identity) as the candidate topology in the summary, the same way the
     DSSG-context block below pre-fills known answers for `nonprofit-success-ai`/`project-mgmt-ai`. This
     maps to `/project-genesis`'s `frontend_backend_topology` question (see §7 table).

5. **Is this a fresh project or layering onto something?**
   - If layering: what already exists and what's off-limits to touch?

6. **Does it need to expose tools to other agents or services?** (→ MCP server)

### Step 3 — Tier 3: AI design

7. **What data does the AI reason over?**
   - Structured records (DB rows)? Unstructured documents (PDFs, transcripts, notes)?
   - Live API data (calendar, email, web)?

8. **How will you evaluate "good"?**
   - Is there a golden set of expected outputs to grade against?
   - Or is quality judged manually / by user feedback?
   - Does quality measurement need to be automated for CI?
   - Capture the answers as concrete metric targets in DESIGN.md's Evaluation table
     (metric, target, how measured) — they become `evals/targets.yaml` in the
     generated project, not just prose.

8b. **What's the naive baseline?**
   - What happens if you build nothing — or solve it with a lookup table, keyword
     search, or a human checklist?
   - What must the AI beat, and by how much, to justify itself? Most AI projects
     fail at planning, not modeling — a project that can't name its baseline
     can't demonstrate value over it.

### Step 4 — Tier 4: Constraints

9. **Data classification:** public / internal / restricted / secret?
   - Any PII or sensitive client data flowing through?

10. **Multi-tenancy:**
    - Must multiple clients/orgs be isolated from each other's data?
    - Is this enforced at the DB layer (RLS) or application layer?

11. **Operator model:**
    - Who runs this after the POC — rotating volunteers, a dedicated team, or the org itself?
    - Budget constraints (free tier only, or paid services acceptable)?

### Step 5 — Tier 5: MVP scope

12. **What's the thinnest slice that demonstrates value?**
    - What must be working for someone to say "yes, this is useful"?

13. **What are the top 2–3 risks this POC should validate?**
    (These become the eval suite's primary grading targets.)

14. **What's explicitly OUT of scope for the POC?**
    (Name it explicitly — prevents scope creep during build.)

### Step 6 — Confirm and write DESIGN.md

Summarize what you've learned back to the user in the DESIGN.md structure below. Get explicit
confirmation before writing. If anything feels like a guess rather than something they actually
said, ask directly.

Write the DESIGN.md to `--output` (default: `.claude/docs/DESIGN.md` if pre-scaffold,
`DESIGN.md` in the project root if already inside a generated project).

### Step 7 — Hand off to /project-genesis

After writing DESIGN.md, surface the `/project-genesis` answers that are now determinable
from the design:

| DESIGN.md answer | /project-genesis question |
|-----------------|--------------------------|
| Actor type + data flow | `primary_chat_agent` |
| External systems to integrate | `include_mcp_server`, integration toggles |
| Data classification | `data_sensitivity` |
| Evaluation rigor | `enable_structure_guard` |
| Existing repo or fresh | `scaffold_full_project` |
| Vector/retrieval needs | `vector_backend` |
| Operator model (budget/scale) | `vector_backend` complexity, `aws_region` |
| System boundaries (external user + own backend) | `frontend_backend_topology` |
| Evaluation table (metrics + targets) | transcribed into `evals/targets.yaml` after render (see /project-genesis Step 4) |

Tell the user: "Run `/project-genesis` next. Here's what to answer for the infrastructure
questions:" — and list the pre-determined values. Questions still open can be answered
interactively during `/project-genesis`.

---

## DESIGN.md structure

```markdown
# System Design — [project_name]

**Date:** YYYY-MM-DD
**Status:** Draft / Confirmed / In-build

---

## Problem + Success Criteria

[1–2 sentences: what problem, who has it, what's the current workaround]

**POC demo target:** [What does someone see in a 5-minute demo that makes them say yes?]

**Naive baseline:** [What's the non-AI alternative (do nothing / keyword search / manual
process), and what must the AI beat, by how much, to justify itself?]

---

## Actors

| Actor | Type | What they do today | What the AI does for them |
|-------|------|--------------------|--------------------------|
| [name] | [internal/external/system] | [current state] | [AI's role] |

---

## System Context (C4 Level 1)

[One paragraph or lightweight mermaid diagram: people + systems + connections.
Don't draw what doesn't exist yet. Containers and components come later, when you're building.]

---

## MVP Scope

**In:**
- [concrete deliverable]
- [concrete deliverable]

**Out (explicitly):**
- [what we're NOT building in POC]

**Open (decide before sprint 1):**
- [decision that's blocking build but not resolved yet]

---

## Key Decisions

| Decision | Status | Choice | Rationale |
|----------|--------|--------|-----------|
| Auth/identity | Resolved / Open | [choice] | [why] |
| Data model ownership | Resolved / Open | [choice] | [why] |
| AI approach (retrieval/gen/automation) | Resolved / Open | [choice] | [why] |
| [other] | | | |

---

## Evaluation

| Metric | Target | How measured |
|--------|--------|--------------|
| [e.g. hit_rate] | [e.g. ≥ 0.8] | [e.g. `make eval-heuristic` vs golden set] |
| [risk-derived metric, from Tier 5 Q13] | | |

[These become `evals/targets.yaml` in the generated project — `make eval-gate`
fails when a metric drops below target. Derive at least one row from each of
the top risks named in Step 5, and one from the naive baseline (what margin
over the baseline justifies the AI).]

---

## Non-Functional Constraints

- **Data classification:** [public / internal / restricted / secret]
- **Multi-tenancy:** [required / not required — enforcement mechanism if required]
- **Operator model:** [who runs this, budget, volunteer vs. dedicated]
- **Scale:** [expected load, SLA if any]
```

---

## DSSG platform context (loaded when DSSG detected in Step 0)

These are already decided for DSSG platform projects — do not re-decide them in the interview:

**Shared infrastructure** (neither project owns alone):
- Supabase Postgres — shared DB, `Business` / `Engagement` / `User` tables, RLS from day one
- Engagement lifecycle: `initial_meeting → budgeting → engagement_tracking → hackathon → membership_close`
- Platform API: shared auth check + engagement read/write (API key per calling service)
- Comms sender: triggered by `Engagement.stage` writes, plain transactional email (not n8n)

**Three actor roles** (all projects share these):
- **NPO Client** (external) — nonprofit partner, sees their own engagement status
- **Data Diplomat** (internal) — cohort volunteer, does the grassroots work with NGOs
- **DSSG core volunteer** (internal) — staff/leads, builds and runs the platform

**Per-project scope:**

*nonprofit-success-ai* (customer portal):
- Actor: NPO Client (external-facing)
- Stage ownership: all stages EXCEPT `hackathon` (portal drives `initial_meeting` → `membership_close`)
- Handoff OUT: when `Engagement.stage` transitions to `hackathon`, project-mgmt-ai takes over
- Current state: React 19 + Firebase Auth + Firestore (no backend server)
- Open decision: Firebase vs. Supabase migration — resolve before adding AI features. If resolved toward
  Supabase, the concrete scaffold is `split_service` (Next.js + FastAPI + Supabase JWT, modeled on
  FOIA-Fluent).
- Multi-tenancy: non-negotiable (RLS required from day one)
- AI scope: to be defined — candidates: engagement summaries, stage suggestions, client chat

*project-mgmt-ai* (lifecycle backend / coordination service):
- Actor: DSSG core volunteers + Data Diplomats (internal/volunteer-facing)
- Stage ownership: `hackathon` stage (receives handoff from portal)
- Handoff IN: `Engagement.stage === 'hackathon'` from nonprofit-success-ai
- Current state: README only — nothing built
- Scope risk: existing 8-sprint proposal is too broad; first task is MVP narrowing
- Auth: must reuse whatever nonprofit-success-ai lands on (one identity system)
- Key open question: which single slice ships first (meeting transcription? task extraction? handoff capture only?)

**For DSSG interview, focus on:**
1. Which project? (portal vs. lifecycle backend)
2. What's the AI doing in this project specifically? (not named in either repo yet)
3. MVP: what's the thinnest demo? (for portal: client sees their engagement status + one AI-generated summary; for lifecycle backend: hackathon handoff captured + team assigned)
4. Firebase vs. Supabase decision (blocks both projects)

---

## Notes

- Don't conflate `/scope-poc` with `/project-genesis`. Design and infrastructure are different
  conversations at different times. Many `/scope-poc` sessions happen before any code exists.
- If the design reveals a need the template genuinely can't scaffold, name it explicitly
  rather than silently dropping it — same discipline as `/project-genesis` and `/new-agent`.
- DESIGN.md is a living doc. Update it when decisions resolve or scope changes. It's not a
  one-time artifact — it's the authoritative record of what this project is for.
