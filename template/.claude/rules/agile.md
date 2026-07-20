# Agile workflow — states, DoR, DoD, cadence

## Issue tracking: GitHub Issues

GitHub Issues is the board. Labels encode workflow state. Plan docs hold thinking.

| Artifact | Format | Example |
|---|---|---|
| Branch | `feature/gh-<num>-<slug>` | `feature/gh-12-add-auth` |
| Commit | `{type}: {desc} (#{num})` | `feat: add auth (#12)` |
| PR title | `#{num} {description}` | `#12 Add auth` |

Labels: `backlog` → `refinement` → `ready` → `in-progress` → `blocked` → `in-review` → closed (Done).

## Definition of Ready

A ticket may be labeled `ready` when ALL hold:

1. Problem stated in one sentence (observed friction, not solution)
2. Acceptance criteria — checkable by someone who didn't scope it
3. Enforcement level chosen (hook > skill > rules > MEMORY.md)
4. Metric named (`absence:` / `count-drop:` / `presence:` / `ratio:`) for tooling changes
5. Sized to one session, or split
6. Dependencies named, none unresolved-blocking

Failing DoR after two refinement passes → back to `backlog` or close.

## Definition of Done

1. Acceptance criteria met — verified by running, not by inspection
2. Tests pass (`make precommit` / `make test`)
3. Human committed (Claude never commits)
4. PR merged, or N/A for local-only tooling
5. Tooling ledger row added (`hypothesis` + metric) for tooling changes
6. Plan doc `Status:` updated to `EXECUTED`

A tooling change is not Done when merged — it is Done when the ledger row exists.

## WIP limit

Three `in-progress` across all repos. One active, one blocked, one in review.

## Cadence

Weekly boundary (not a sprint):
- `/workflow-insights` → `/workflow-retro`
- `hypothesis` rows older than 2 weeks get a verdict or explicit extension
- Backlog reordered
- Cycle time read from issue creation → close

## Ceremony → skill mapping

| Ceremony | Skill | Writes |
|---|---|---|
| Refinement | `/workflow-refine` (batch) or `/workflow-research` → `/workflow-plan` (per-item) | DoR check → label `ready` |
| Execution | `/workflow-execute` | code + plan doc |
| Review | `/code-review`, `/workflow-review` | label `in-review` |
| Retro | `/workflow-retro` | findings → issues (stop/improve) or ledger (keep) |
