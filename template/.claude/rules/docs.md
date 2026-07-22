# Documentation Rules — the audience split

Two doc audiences, two writers. No third writer.

## Machine-consumed docs

**What:** `.claude/` contents (skills, hooks, plans, session/handover docs), `CLAUDE.md`
files, `~/.claude/rules/*.md`, `SANYI.md` contracts, `MEMORY.md`.

**Who writes:** the feedback loop (sessions, `/retro` proposals) — always as reviewed
diffs, never silent edits. Ramsey commits.

**Formats:**
- Plan docs carry a `Status:` line (PLANNED / IN PROGRESS / EXECUTED / ABANDONED) so
  /wake, /retro, and /config-audit can read state without parsing prose.
- One work doc per item: `.claude/docs/plans/YYYY-MM-DD-<slug>.md` — prefix the slug
  with `lin-<id>-` when a Linear issue exists (`2026-07-17-lin-12-add-auth.md`).
  Research, plan, and review are sections of that one file. No SESSION.md, no
  in-progress/ — dated filenames + Status lines make the directory self-indexing;
  active doc = `grep -l 'Status: IN PROGRESS' .claude/docs/plans/*.md`.
- `.claude/docs/` is git-ignored everywhere (`~/.gitignore_global`, decided
  2026-07-17): plan docs, `state/`, and the tooling ledger are local-only working
  files with no git history. Never reference them from committed docs (READMEs,
  code comments) — clones won't have them — and never bulk-delete them: gone is
  gone, there's no history to restore from.
- Size ceilings: ledgers and index files stay under ~1 screen — compress, don't grow.
- Cross-document state is referenced by pointer (path + Status line), never copied —
  copies go stale silently. (Graduated from puffin growth.md, 2026-07-17: a copied
  work queue drifted across 3 handovers before the divergence was caught.)
- Write targets by enforcement strength: hooks > skills/protocols > CLAUDE.md/rules >
  MEMORY.md. Codify at the strongest level that fits.
- Skill placement: global (`~/.claude/skills/`) is canonical for anything generic; a
  repo `.claude/skills/` holds only repo-specific skills (project pipelines, guacamayo's
  identity-lifecycle set: wake/grow/reflect/synthesize/dream/intermission/genesis — they
  write to `.sounding/`). Same-name collisions with global are config drift (/config-audit
  Check 1).

## Human-consumed docs

**What:** READMEs, design docs (`DESIGN.md`, RFCs), the librarian wiki, portfolio and
learning-repo pages.

**Who writes:** humans, or librarian's compile pipeline (raw/ → wiki). Sessions may
**flag** staleness or drift (docs_hygiene hook, review findings) but do not write these
directly — an agent-edited README that nobody reviewed is worse than a stale one.

**akira exception (`/akira dao` only).** akira — and only akira, running its `dao` mode —
may *edit* human-consumed docs, not just flag them. This is a deliberate carve-out of the
flag-only rule above; it does not generalize to other sessions or agents. It is safe
because:
- Edits land in the **working tree only, never committed** — the mandatory human commit
  step (Ramsey commits, always) is the review-before-publish valve, not a read-only rule.
- akira first looks for that repo's **doc-style reference** (the repo's `Refs:` line
  pointing at a docs-style ref, or repo-local stakeholder guidelines) and conforms to it.
  There is intentionally **no global `~/.claude/refs/docs-style.md`** default (decided
  2026-07-18) — no single repo's style is asserted as universal.
- **No style ref found → akira still edits, but flags it prominently in its run report**
  as a human-doc edit made without a style guide, so the human reviewer knows to check
  tone/conventions before committing.

Every non-akira session still treats human docs as **flag-only**.

## Boundary cases

- A repo's `CLAUDE.md` is machine-consumed even though humans read it — the loop may
  propose diffs to it.
- Wiki pages about tooling (e.g. the SANYI page) are human-consumed: they enter through
  librarian's ingest of the machine-consumed sources, not by direct session edits.
- When unsure, ask: "who acts on this file — Claude in a future session, or a person?"
  Claude → loop writes it (reviewed). Person → flag, don't write.
