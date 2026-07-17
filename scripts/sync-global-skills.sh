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

SKILLS=(
  quick-commit
  quick-pr
  review-pr
  execute-tasks
  scope-initiative
  design-sprint
  doc-to-linear-tickets
  plan-review
  research-review
  execute-plan
  code-review
  code-debug
  compact-session
  define-milestones
  github-projects
  mcp-builder
  plan-refactor
  prototype
  skill-creator
  sanyi
)

changed=()
for skill in "${SKILLS[@]}"; do
  src="$RESERVOIR/$skill"
  dst="$TEMPLATE_ROOT/$skill"

  if [ ! -d "$src" ]; then
    echo "warning: $skill missing from reservoir ($src) — skipping" >&2
    continue
  fi

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
