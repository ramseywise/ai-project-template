#!/usr/bin/env bash
# Syncs the shared workflow skills from the global reservoir (~/.claude/skills/)
# into this template's vendored copy (template/.claude/skills/).
#
# One-way: reservoir -> template, never the reverse. ~/.claude/skills/ is
# canon (edit it directly); run this script, then commit the result here,
# whenever the reservoir changes and the template should pick it up.
set -euo pipefail

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
    rm -rf "$dst"
    cp -R "$src" "$dst"
  fi
done

if [ ${#changed[@]} -eq 0 ]; then
  echo "No changes — template already matches the reservoir."
else
  echo "Synced ${#changed[@]} changed skill(s):"
  printf '  %s\n' "${changed[@]}"
  template_repo="$(cd "$TEMPLATE_ROOT/../../.." && pwd)"
  echo "Review with: git -C $template_repo diff"
fi
