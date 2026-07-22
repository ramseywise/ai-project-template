# Review Report Template

Produced by the orchestrator after dispatching reporters, merging findings, and
assessing DoD. Adapted for our two-reporter model (akira-scan + SANYI) rather than
Parallax's 7-subagent model.

```markdown
# Review Report

## 1. Overall Understanding

[1-3 sentences: what this change does, its context, and its risk level]

## 2. Review Contract

[From context brief: intended change, scope, constraints, review profile]

## 3. What Looks Strong

[Genuine positives — good patterns, solid test coverage, clean architecture.
Not filler. If nothing stands out, skip this section.]

## 4. Blocking Findings

[merge_impact: blocker — must be resolved before merge]

## 5. Important Findings

[merge_impact: important — should be addressed or consciously accepted]

## 6. Questions and Hypotheses

[merge_impact: question — missing context prevents judgment.
Also hypothesis-state findings that need investigation.]

## 7. Suggestions and Nits

[merge_impact: suggestion | nit — improvements, not requirements]

## 8. Testing and Evaluation Assessment

[Test coverage for changed code. Gaps identified. For agent/judgment code:
were repeated runs considered?]

## 9. Definition of Done Assessment

| Item | Status | Note |
|------|--------|------|
| Intended behavior complete | met / gap / n/a | |
| Edge cases handled | met / gap / n/a | |
| Tests sufficient | met / gap / n/a | |
| Documentation updated | met / gap / n/a | |
| Observability present | met / gap / n/a | |
| Security reviewed | met / gap / n/a | |
| Rollback understood | met / gap / n/a | |
| Limitations recorded | met / gap / n/a | |

## 10. Reporter Dispatch Summary

| Reporter | Status | Findings |
|----------|--------|----------|
| akira-scan (quality) | dispatched / skipped | N findings (B blocking, I important) |
| SANYI (contracts) | dispatched / skipped (no SANYI.md) | N findings |
| lint/tests | ran / skipped | pass / fail |

[If a reporter failed: note what was missed and whether it affects verdict confidence.]

## 11. Merge Verdict

**approve** | **comment** | **request_changes** | **insufficient_context**

[1-2 sentence rationale. If request_changes: list the blocking finding IDs.]
```

## Verdict rules

- Any `merge_impact: blocker` finding → `request_changes`
- Only `important` + `suggestion` + `nit` findings → `comment`
- No findings or only nits → `approve`
- Reporter failures that could mask blockers → `insufficient_context`
- `question`-only findings (no blockers) → `comment` (questions don't block)
