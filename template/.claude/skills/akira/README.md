# akira

**An interactive code-quality scanner with actuation.** akira reads a codebase
or diff, surfaces findings ranked by severity, asks the questions the change
leaves unanswered, and — in dao mode — applies safe fixes with a test gate.

Named after the film: Kaneda (yang) hunts concrete defects; Kiyoko (yin) asks
the questions no one thought to ask. Dao is the path from findings to a fixed
working tree.

## Modes

| Mode | What it does | Subagent |
|------|-------------|----------|
| `scan` | Read-only ranked findings across 9 categories | `akira-scan` (haiku, parallel batches) |
| `wander` | 3-5 sharp questions about what the change leaves open | `akira-wander` (haiku) |
| `dao` | Triage findings → apply safe fixes → test → revert on fail → doc-sync | Inline (test-gated, see `references/dao.md`) |
| `all` | wander → scan → dao in sequence | All of the above |
| `auto` | Classify changed set, skip modes with nothing to bite, end at dao | Adaptive |

```
/akira              # defaults to scan
/akira wander       # or /akira ?
/akira dao          # test-gated actuation
/akira all          # full pipeline
/akira auto         # adaptive
/akira scan repo:listen-wiseer   # target a specific repo
/akira dao headless              # non-interactive (for spawned agents)
```

## Relationship to other review tools

akira is a **standalone tool** — it can be invoked directly for interactive
quality review. It is also **composed by orchestrators**:

- `/code-review level:2` spawns akira-scan as part of its pipeline
- `/code-review level:3` adds full `/sanyi` on top
- `/workflow-review` uses the same composition for PR review

akira and `/sanyi` are complementary lenses:
- **akira** asks "is this any good?" — structure, patterns, decisions, quality
- **sanyi** asks "did this move a boundary?" — contract violations, layer drift

## The dao contract

dao is the only mode that modifies code. It is test-gated:

1. Triage all findings into **low-radius** (auto-apply) vs **high-radius** (surface-only)
2. Apply low-radius fixes one at a time
3. Run the test suite after each fix
4. If tests fail: revert that specific hunk, record it, move on
5. High-radius findings are reported with recommendations, never auto-fixed
6. Buyi (invariant) findings from SANYI are **never** auto-fixed — by design

The tree is always green when dao finishes. See `references/dao.md` for the
full contract.

## Scan categories

akira-scan covers 9 categories per file batch (see `agents/akira-scan.md`):
bugs/logic errors, missing safeguards, complexity/dead code, naming/layering,
config/secrets hygiene, error/resource handling, data-correctness (path-gated),
prompt/LLM smells (path-gated), test-shape (path-gated).

Findings use canonical format: `**[merge_impact:evidence_state]** AK-NNN file:line`.

## Evals

Two tiers (see `evals/README.md`):

1. **Trigger eval** (`evals/trigger-eval.json`) — 20 queries testing dispatch
   accuracy. Should-trigger on quality/review/fix requests; should-not-trigger
   on `/sanyi audit`, `/code-review`, `make test`, commit/refactor requests.

2. **Behavioral eval** (`evals/evals.json`) — 3 judgment-path cases:
   - `wander-question-quality` — names decisions the diff walked past, not restates code
   - `dao-triage-tiering` — dead import = low, contract change = high
   - `dao-revert-on-failure` — reverts broken fix, leaves green tree

   Run N=3-5 times with variance analysis. Judgment skills need statistical
   confidence, not single-run pass/fail.

## References

| File | Contents |
|------|----------|
| `references/modes.md` | Kaneda/Kiyoko/dao family taxonomy |
| `references/dao.md` | Test-gated actuation contract |
| `references/behavioral-eval-scaffold.md` | Reusable eval pattern for judgment-shaped skills |
