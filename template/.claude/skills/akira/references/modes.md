# akira — the mode family

akira is not one subagent; it is a family with two temperaments and a path that walks
between them. The name is a family label, not a single scanner.

## The two temperaments

| | **Kaneda (yang)** | **Kiyoko (yin)** |
|--|--|--|
| Mode | `scan` | `wander` |
| Agent | `akira-scan` | `akira-wander` |
| Asks | "What is broken here?" | "What did this change leave unanswered?" |
| Returns | ranked findings (`file:line — issue — severity`) | 3–5 pointed questions |
| Mutates | no | no |
| Shape | parallel fan-out over file batches | one pass over the diff |

They are complements. scan finds the defect; wander finds the *decision the author walked
past*. Run wander before scan when you want to interrogate intent before hunting bugs;
run scan alone when you just want a defect list.

## The path

`dao` (道) is the path from findings to a fixed, tested working tree. It is **not** a
subagent — it runs inline in the session because it mutates the tree and drives an
apply→test→revert loop that a subagent can't safely hand back clean. dao consumes scan's
findings, triages them by blast radius, applies only the safe ones behind a test gate,
and syncs docs. See `dao.md` for the full contract.

## Full flow and sweep

**Bare `/akira`** = full flow: wander → scan → sanyi → dao. Scope is automatic: if a diff
exists (uncommitted + branch changes), scope = diff. If clean, scope = whole repo (scan
fans out over all tracked files, wander skips, sanyi runs audit).

**`/akira all`** = repo sweep. Runs the full flow across all included repos sequentially.
Not a mode — a scope directive. Each repo gets independent scope detection. Results
aggregate into a cross-repo summary table.

Included repos: guacamayo, job-system, learn-ai-engineering, librarian, atlas,
ai-project-template, listen-wiseer.

## Why one skill, not three

The primitives share scope detection, repo resolution, and the report format. Splitting
them into three skills would duplicate that shared setup and hide the family relationship.
One `/akira` skill, 3 primitive tokens + full flow + sweep.

## Relationship to the other review tools

- **`/review-sweep`** — the *standing report*. Runs the same `akira-scan` quality scan
  (plus lint/tests/SANYI/doc-flags) and writes a report. akira is its *interactive,
  actuating sibling*: `scan` gives the same findings, but `wander` and `dao` add the
  question and fix modes review-sweep doesn't have.
- **`/code-review`** — plan-fidelity review of a specific work item against its plan doc.
  akira is diff-shaped and plan-agnostic.
