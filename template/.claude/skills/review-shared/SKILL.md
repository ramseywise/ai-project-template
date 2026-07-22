---
name: review-shared
description: >
  Cross-cutting review infrastructure — evidence model, finding schema, merge/dedup
  logic, DoD assessment, context brief and report templates. Preloaded by review
  orchestrators and agents via skills: [review-shared]. Not invoked directly.
allowed-tools: Read
---

# Review Shared

Shared review infrastructure consumed by orchestrators (`/code-review`, `/workflow-review`) and
agents (`akira-scan`, `akira-wander`) via `skills: [review-shared]` in their frontmatter.
This skill is read-only knowledge — it never acts, only informs.

## Evidence classification

All findings carry an `evidence.state` field. See `~/.claude/refs/evidence-model.md` for
the full model. Summary:

| State | Meaning | Phrasing rule |
|-------|---------|--------------|
| verified | Confirmed by code/test/trace/contract | State as fact |
| supported | Strong evidence, one assumption remains | State as likely |
| hypothesis | Plausible, insufficient evidence | "This appears to..." — never as confirmed defect |
| question | Missing context prevents judgment | Phrase as clarification request |

Evidence state is **orthogonal** to severity. A hypothesis can be a blocker.

## Severity vs merge impact

Two separate fields in the canonical schema (`~/.claude/refs/finding-schema.md`):

- **`source_native`** — the reporter's own severity, preserved verbatim. akira uses
  `Blocking/Non-blocking/Nit`; SANYI uses violation codes (`BY-2 blocker`, `JY-1 warning`).
  Never invent or rewrite another system's codes.
- **`merge_impact`** — PR-level impact: `blocker | important | question | suggestion | nit`.
  Reporters propose this using default mappings (see finding-schema.md); orchestrators may
  adjust during merge.

## Merge and deduplication

When multiple reporters produce findings, the orchestrator merges them:

1. **Group** findings by `location.file` + `location.lines` overlap (within 5 lines)
   AND category similarity (same dimension or scan category)
2. **Judge** whether grouped findings describe the same underlying issue. Same file+line
   is necessary but not sufficient — two distinct issues at the same location stay separate.
3. **Merge** confirmed duplicates:
   - Preserve all source IDs (e.g. `AK-003 + SY-001`)
   - Use the most precise root cause (prefer the reporter with deeper analysis)
   - Take the higher `merge_impact`
   - Take the more certain `evidence.state`
   - Preserve SANYI violation codes as `source_native`
4. **Report** merged findings with provenance: which reporters contributed

## DoD assessment

See `~/.claude/refs/review-dod.md` for the checklist. The orchestrator checks each item
as `met`, `not applicable`, or `gap`. Gaps become findings with appropriate merge_impact.
Repo-specific DoD overrides the default.

## Communication rules

- Findings with `evidence.state: hypothesis` must be phrased as hypotheses, not confirmed
  defects. "This might..." not "This is broken."
- Findings with `evidence.state: question` are clarification requests, not accusations.
- `merge_impact: blocker` findings use `communication.comment_type: request_change`.
- All other findings use `suggestion`, `question`, or `nit` as appropriate.

## Templates

- **Context brief**: `references/context-brief.md` — produced once by orchestrator, passed
  to all dispatched reporters. A reporter should never need to re-derive repo context.
- **Review report**: `references/review-report.md` — unified report template for the
  orchestrator's final output after merge/dedup and DoD assessment.

## Refs consumed

This skill depends on four refs (read them for full specifications):
- `~/.claude/refs/finding-schema.md` — canonical finding format
- `~/.claude/refs/evidence-model.md` — evidence classification
- `~/.claude/refs/review-dimensions.md` — dimension checklists for multi-perspective review
- `~/.claude/refs/review-dod.md` — Definition of Done for reviews
