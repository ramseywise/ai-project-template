# System Design — My Project

**Date:** <!-- fill in -->
**Status:** Draft

> This file is your project's authoritative design record. Populate it before
> or alongside scaffolding — ideally by running `/scope-poc` first, which runs
> a structured interview and writes this file for you. If you're starting here
> directly, fill in each section before sprint 1. A blank DESIGN.md is a signal
> that key decisions haven't been made yet, not that they don't matter.

---

## Problem + Success Criteria

<!-- 1–2 sentences: what problem, who has it, what's the current workaround -->

**POC demo target:** <!-- What does someone see in a 5-minute demo that makes them say yes? -->

**Naive baseline:** <!-- What's the non-AI alternative (do nothing / keyword search /
manual process), and what must the AI beat, by how much, to justify itself? -->

---

## Actors

| Actor | Type | What they do today | What the AI does for them |
|-------|------|--------------------|--------------------------|
| <!-- name --> | internal <!-- from scaffold: refine --> | <!-- current state --> | <!-- AI's role --> |

---

## System Context

<!-- One paragraph or lightweight mermaid diagram: people + systems + connections.
     Draw only what exists or will exist in this POC — not the full future state. -->

**External systems (from scaffold):** none declared

---

## MVP Scope

**In:**
-

**Out (explicitly):**
-

**Open (decide before sprint 1):**
-

---

## Key Decisions

| Decision | Status | Choice | Rationale |
|----------|--------|--------|-----------|
| Auth / identity | <!-- Resolved / Open --> | | |
| Data model ownership | <!-- Resolved / Open --> | | |
| AI approach | Resolved | mcp_server | Set at scaffold time — revisit if the shape changes |
| Data sensitivity | Resolved | internal | Set at scaffold time |
| Deployment target | Resolved | serverless | Set at scaffold time |
| Multi-tenancy | <!-- Resolved / Open --> | | |

---

## Evaluation

| Metric | Target | How measured |
|--------|--------|--------------|
| <!-- e.g. hit_rate --> | <!-- e.g. ≥ 0.8 --> | <!-- e.g. `make eval-heuristic` vs golden set --> |

<!-- These targets become evals/targets.yaml — `make eval-gate` fails when a metric
     drops below target. Derive at least one row from each top risk in MVP Scope,
     and one from the naive baseline (what margin over it justifies the AI).
     SANYI layer note: the threshold VALUES are 变易 Bianyi (tune freely in
     targets.yaml, no deploy); "the eval gate must run before release" is 不易
     Buyi — record it in SANYI.md once wired into CI. -->

---

## Non-Functional Constraints

- **Data classification:** internal
- **Multi-tenancy:** <!-- required / not required; if required: enforcement mechanism -->
- **Operator model:** <!-- who runs this after POC, budget, volunteer vs. dedicated team -->
- **Scale:** <!-- expected load, any SLA -->

---

## Open Questions

<!-- Things that surfaced during design but weren't resolved. Resolve these before sprint 1,
     not during. Each unresolved question here is a risk to POC delivery. -->

-

---

*Populated by `/scope-poc`. Updated as decisions resolve. Never deleted — this is the record
of what the project is for, not just what it does.*
