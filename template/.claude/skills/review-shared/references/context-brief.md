# Context Brief Template

Produced once by the orchestrator (`/workflow-review` or `/code-review`), passed to every
dispatched reporter. A reporter should never need to re-derive any of this itself.

```markdown
# Review Context Brief

## Review Contract

- Intended change: [what the PR/diff claims to do]
- Expected behavior: [what should be true after merge]
- Scope: [what's in scope for this review]
- Out of scope: [what to ignore]
- Constraints: [repo conventions, CLAUDE.md rules, SANYI.md contracts]
- Confirmed facts: [things verified by reading code/docs]
- Inferred assumptions: [things assumed but not confirmed]
- Unknowns: [things we can't determine from available context]
- Initial risk areas: [where to look hardest]
- Review profile: general | agent-system
  [general: dimensions 1-5 only. agent-system: all 7 dimensions.
   Infer from imports/file paths if not stated by user.]

## Repository Context

- Repository purpose: [from CLAUDE.md / README]
- Stack: [languages, frameworks, key dependencies]
- Repo conventions: [from CLAUDE.md — naming, layering, refs]
- SANYI contract: [exists | does not exist. If exists: summary of layers]
- CI status: [passing | failing | unknown]
- Changed files: [list with brief role description]
- Nearby files: [files that interact with changed files]
- Callers of changed symbols: [who calls what was changed]

## Change Map

- Input: [what enters the changed code]
- Validation: [how input is validated]
- Transformation: [what the code does to data]
- State transition: [what state changes]
- External systems: [APIs, databases, services touched]
- Side effects: [writes, notifications, logs]
- Error path: [what happens on failure]
- Output: [what leaves the changed code]
```

## Usage

The orchestrator fills this template by reading:
1. PR metadata (`gh pr view`) or `git diff` + `git log`
2. Repo CLAUDE.md and SANYI.md (if present)
3. Changed files and their callers (Grep for symbol references)
4. CI status (`gh pr checks` or `make test`)

Missing context is not a code defect. If a field is unknown, write "unknown" and
let the intent dimension raise it as a question finding.
