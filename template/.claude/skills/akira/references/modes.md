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

## `all` and `auto`

`all` = wander → scan → dao, unconditionally. "Look at this properly, run everything."

`auto` = the same family, routed. It classifies the changed set and skips modes that have
nothing to act on — scan is skipped when nothing executable changed — but **always ends at
dao**, because dao is the only mode that actuates. dao's test gate is untouched by routing:
skipping scan changes what dao is given to work from, never whether it is allowed to mutate.

Prefer `auto` as the default entrypoint; reach for `all` when you want to force a scan the
router would have skipped.

## Why one skill, not three

The modes share diff-scoping, repo resolution, and the report format, and they compose
(`all`). Splitting them into three skills would duplicate that shared setup and hide the
family relationship. One `/akira` skill, four mode tokens.

## Relationship to the other review tools

- **`/review-sweep`** — the *standing report*. Runs the same `akira-scan` quality scan
  (plus lint/tests/SANYI/doc-flags) and writes a report. akira is its *interactive,
  actuating sibling*: `scan` gives the same findings, but `wander` and `dao` add the
  question and fix modes review-sweep doesn't have.
- **`/code-review`** — plan-fidelity review of a specific work item against its plan doc.
  akira is diff-shaped and plan-agnostic.
