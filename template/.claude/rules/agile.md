# Agile workflow — states, DoR, DoD, cadence

## Issue tracking: GitHub Issues

GitHub Issues is the board. Labels encode workflow state. Plan docs hold thinking.

### Strict gates

1. **No code changes without a GitHub issue.** Every planned change needs an issue first.
   Exceptions: `bug/` branches (quick fixes) and `spike/` branches (exploration).
2. **Always on a branch, never main.** No direct commits to main/master.
3. **Claude never pushes.** Stage changes, commit on branch. Ramsey reviews staged
   commits, adjusts if needed, pushes.
4. **Parallax is read-only.** No changes to that repo.

### Branch naming

| Type | Format | Example | Requires |
|------|--------|---------|----------|
| Feature/planned | `{PREFIX}-{NUM}-{slug}` | `GUA-9-workflow-simplification` | GitHub issue + plan doc |
| Bug fix | `bug/{slug}` | `bug/fix-broken-links` | None (create issue if non-trivial) |
| Spike | `spike/{slug}` | `spike/explore-supabase` | None |

### Repo prefix table

| Prefix | Repo |
|--------|------|
| GUA | guacamayo |
| LAE | learn-ai-engineering |
| LIS | listen-wiseer |
| ATL | atlas |
| PLG | playground |
| AIT | ai-project-template |
| LIB | librarian |
| LEB | lebanese-blonde |
| JOB | job-system |
| DSG | dssg |

### Commit messages

Conventional commits with issue reference. Type is required; scope is optional.

```
{type}({scope}): {description} (#{num})
```

| Type | When |
|------|------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `refactor` | Restructure without behavior change |
| `docs` | Documentation only |
| `chore` | Maintenance, config, dependencies |
| `test` | Tests only |
| `style` | Formatting, linting (no logic change) |

Examples:
```
feat(review): merge code-pr into workflow-review (#9)
fix: broken relative links after notes move (#25)
chore: compress tooling ledger to 30 lines (#9)
docs: update CLAUDE.md skill groups
```

`(#{num})` auto-links to the issue in the same repo. Omit for bug/spike branches without issues.

### PR title

```
{PREFIX}-{NUM} {description}
```
Example: `GUA-9 Workflow simplification: merge code-pr into workflow-review`

Labels: `backlog` → `refinement` → `ready` → `in-progress` → `blocked` → `in-review` → closed (Done).

### PR body convention

PR bodies must include `Closes #N` for every issue the PR resolves. GitHub auto-closes
on merge — no manual closure needed. The `make quick-pr` target extracts issue numbers
from commit messages and generates the `Closes` lines automatically.

### Agent spawn conventions

Worktree agents MUST include a commit step in their prompt:
`git add -A && git commit -m "{type}: {description} (#{num})"`
Non-worktree agents stage only (caller reviews before committing).

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
2. Tests pass (`make lint` / `make test`)
3. On a named branch (never main) — human committed (Claude never commits)
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
| Groom | akira wander, manual, `/workflow-retro` findings | issue (labeled `backlog`) |
| Research | `/workflow-research` (if needed) | research artifact in plan doc |
| Plan | `/workflow-plan` | plan doc with steps |
| Refine | `/workflow-refine` — DoR gate | label `ready` |
| Execute | `/workflow-execute` | code + plan doc |
| Review | `/code-review`, `/workflow-review` | label `in-review` |
| Ship | `make lint` → `make test` → `make push` → `make ship` | PR + merge |
| Retro | `/workflow-retro` | findings → issues (stop/improve) or ledger (keep) |
