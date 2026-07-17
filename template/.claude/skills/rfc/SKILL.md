---
name: rfc
description: >
  Compile RFC.md — the discovery exit document: a thin approval cover-sheet
  pointing at DESIGN.md, the milestone doc, and M1 TASKS.md for a human
  go/no-go on the MVP plan. Use at the end of discovery, before /gate-check's
  G1 audit. Triggers on: "write the RFC", "discovery exit doc", "ready for
  approval", "compile the proposal", "/rfc".
---

# rfc

RFC.md is a **cover-sheet, not a compilation**. It links the real artifacts and
summarizes each in one line — it never copies their content (cross-document
state travels by pointer; copies go stale silently). A person reads it in two
minutes, follows the links that need scrutiny, and flips one Status line.

## Process

### 1. Locate the artifacts

| Artifact | Where | If missing |
|---|---|---|
| DESIGN.md | project root (or `.claude/docs/DESIGN.md` pre-scaffold) | stop — run `/scope-poc` first |
| Milestones | `.claude/docs/milestones/` or DESIGN.md roadmap section | stop — run `/define-milestones` |
| M1 tasks | TASKS.md / first-sprint plan | stop — run `/sprint-kickoff` |
| Plan review | review note covering the above | flag as missing in the RFC — G1 checks it |

### 2. Write RFC.md at project root

```markdown
# RFC — [project_name] MVP

**Date:** YYYY-MM-DD
**Status:** PROPOSED

## What's proposed

[One paragraph, plain language: the problem, the thinnest slice that
demonstrates value, and what "good" will be measured by. Written for the
approver, not the builder.]

## The plan, by pointer

| Artifact | Path | State |
|---|---|---|
| System design | DESIGN.md | [Status line + date] |
| Milestones | [path] | [N milestones, M1 named] |
| First sprint | TASKS.md | [N tasks, reviewed: yes/no] |
| Eval targets | evals/targets.yaml | [N metrics seeded] |

## Known gaps

- Open questions: [N] blocking, [N] deferred with triggers (see DESIGN.md)
- [anything the approver should weigh — missing review, unresolved risk]

## Approval

Approved by: ______  Date: ______
[A person flips Status to APPROVED and fills this line. Sessions never do.]
```

### 3. Report

Tell the user RFC.md is ready for review, name the approver action (flip
`Status: PROPOSED` → `Status: APPROVED`), and that `/gate-check` mirrors the
result into LIFECYCLE.md's `rfc_approved`.

## Rules

- **Never write `Status: APPROVED`** — not on create, not on regenerate. That
  line is human-only (doc-writer boundary); `/gate-check` only mirrors it.
- **Regeneration preserves approval state:** if RFC.md exists, update the
  pointers, summary, and gap counts — but keep the existing Status line and
  Approval block verbatim. If the plan changed materially after approval, say
  so and ask whether the human wants to reset Status to PROPOSED; never reset
  it silently.
- **One screen.** If a section is growing prose, its content belongs in the
  artifact it points to.

---

**Upstream:** `/scope-poc`, `/define-milestones`, `/sprint-kickoff`, `/plan-review`
**Next:** human approval → `/gate-check` (G1 audit) → delivery phase
