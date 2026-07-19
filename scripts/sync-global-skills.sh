#!/usr/bin/env bash
# Syncs the shared workflow skills from the global reservoir (~/.claude/skills/)
# into this template's vendored copy (template/.claude/skills/).
#
# One-way: reservoir -> template, never the reverse. ~/.claude/skills/ is
# canon (edit it directly); run this script, then commit the result here,
# whenever the reservoir changes and the template should pick it up.
#
# --dry-run: print what would change (with per-file detail) without writing.
set -euo pipefail

DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

RESERVOIR="$HOME/.claude/skills"
TEMPLATE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/template/.claude/skills"

# Reservoir skill names. These MUST match ~/.claude/skills/ exactly — a name that
# drifts out of the reservoir is a hard error below, not a warning (2026-07-19: 13
# pre-rename names sat here unnoticed after the code-/design-/workflow-/git- rename,
# so the template kept shipping stale copies while the renamed skills never synced).
#
# Deliberately NOT synced — template-owned, no global counterpart:
#   execute-tasks, doc-to-linear-tickets  (TASKS.md / Linear, template-specific)
# Retired: compact-session -> ~/.claude/rules/context-health.md
SKILLS=(
  git-commit
  git-pr
  code-pr
  code-refactor
  code-review
  code-debug
  workflow-research
  workflow-plan
  workflow-execute
  design-sprint
  design-initiative
  design-milestones
  design-prototype
  github-projects
  mcp-builder
  skill-creator
  sanyi
)

# Fail fast on any name that no longer exists in the reservoir. Skipping with a
# warning lets a renamed skill rot in the template indefinitely — the warning
# scrolls past, the exit code stays 0, and stale copies keep shipping.
missing=()
for skill in "${SKILLS[@]}"; do
  [ -d "$RESERVOIR/$skill" ] || missing+=("$skill")
done
if [ ${#missing[@]} -gt 0 ]; then
  echo "error: ${#missing[@]} skill(s) in SKILLS[] are not in the reservoir ($RESERVOIR):" >&2
  printf '  %s\n' "${missing[@]}" >&2
  echo "Renamed? Update SKILLS[] in this script. Retired? Remove it there and" >&2
  echo "git rm the stale template/.claude/skills/ copy." >&2
  exit 1
fi

changed=()
for skill in "${SKILLS[@]}"; do
  src="$RESERVOIR/$skill"
  dst="$TEMPLATE_ROOT/$skill"

  if ! diff -rq "$src" "$dst" >/dev/null 2>&1; then
    changed+=("$skill")
    echo "$skill:"
    # what moved, before overwriting — direction is always reservoir -> template
    # (diff exits 1 on difference; don't let pipefail kill the run)
    { diff -rq "$dst" "$src" 2>&1 || true; } | head -8 | sed 's/^/    /'
    if [ "$DRY_RUN" -eq 0 ]; then
      rm -rf "$dst"
      cp -R "$src" "$dst"
    fi
  fi
done

if [ ${#changed[@]} -eq 0 ]; then
  echo "No changes — template already matches the reservoir."
elif [ "$DRY_RUN" -eq 1 ]; then
  echo "[dry-run] ${#changed[@]} skill(s) would sync: ${changed[*]}"
else
  echo "Synced ${#changed[@]} changed skill(s): ${changed[*]}"
  template_repo="$(cd "$TEMPLATE_ROOT/../../.." && pwd)"
  echo "Review with: git -C $template_repo diff"
fi
