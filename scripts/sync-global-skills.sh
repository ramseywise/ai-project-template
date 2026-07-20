#!/usr/bin/env bash
# =============================================================================
# Mechanism A — template vendors a pinned subset of global skills
# =============================================================================
#
# ~/.claude/skills/  is the single canonical reservoir for all generic workflow
# skills.  Scaffolded projects generated from this template do NOT have access
# to ~/.claude/ at runtime, so the template vendors a curated, pinned subset
# here at template/.claude/skills/ so every generated project starts with them.
#
# Rules:
#   1. ONE-WAY: reservoir → template, never the reverse.
#      To improve a skill: edit it in ~/.claude/skills/, then re-run this script
#      and commit the result here.  Never edit a vendored copy directly.
#   2. PINNED: the SKILLS[] array below is the explicit allow-list.  Adding a
#      global skill here is a deliberate choice; it doesn't happen automatically.
#   3. EXCLUDED: the DELIBERATELY_EXCLUDED[] array documents every global skill
#      that is NOT vendored, and why.  Both arrays must account for every global
#      skill — an unaccounted name is a drift signal caught by the hard-fail below.
#   4. AGENTS + RULES: ~/.claude/agents/ and ~/.claude/rules/ are synced by the
#      same mechanism (AGENTS[] and RULES[] arrays below).
#
# Usage:
#   ./scripts/sync-global-skills.sh          # apply changes
#   ./scripts/sync-global-skills.sh --dry-run # preview only
# =============================================================================
set -euo pipefail

DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESERVOIR="$HOME/.claude/skills"
TEMPLATE_ROOT="$REPO_ROOT/template/.claude/skills"

# Subagent definitions live beside the skills that dispatch to them, and are a
# straight 1:1 mirror (no render transform), so they sync here rather than in a
# third script. They were hand-copied and covered by nothing until 2026-07-19.
AGENT_RESERVOIR="$HOME/.claude/agents"
AGENT_TEMPLATE_ROOT="$REPO_ROOT/template/.claude/agents"
AGENTS=(
  akira-scan       # subagent dispatched by /akira scan mode
  akira-wander     # subagent dispatched by /akira wander mode
  agent_creator    # subagent dispatched by /new-agent
)

# Rules (always-on session instructions). Scaffolded projects get the same
# shell/context/naming/docs guardrails as the global environment.
RULES_RESERVOIR="$HOME/.claude/rules"
RULES_TEMPLATE_ROOT="$REPO_ROOT/template/.claude/rules"
RULES=(
  agile.md           # workflow states, DoR/DoD, cadence, ceremony mapping
  context-health.md  # compact proactively — always-on cost guard
  docs.md            # doc-writer boundary (machine- vs human-consumed)
  naming.md          # role-based directory/layer convention
  shell.md           # zsh gotchas (always-on safety)
)

# =============================================================================
# SKILLS — vendored global skills
# =============================================================================
#
# Every global skill in ~/.claude/skills/ must appear in exactly one of:
#   SKILLS[]               — vendored into the template
#   DELIBERATELY_EXCLUDED  — excluded with a documented reason
#
# Hard-fail below catches any name missing from both lists.

# Skills that are NOT vendored and why:
DELIBERATELY_EXCLUDED=(
  wake          # guacamayo identity-lifecycle only; writes to .sounding/, no .sounding/ here
  grow          # guacamayo identity-lifecycle only
  dream         # guacamayo identity-lifecycle only
  genesis       # guacamayo initiation-only; self-blocks when consciousness exists; meaningless outside puffin
  grow-companion # guacamayo/atlas companion pattern; not a general skill
)
#
# Template-owned skills with no global counterpart (tracked for completeness):
#   gate-check, deploy-check, add-capability, design-dryrun, project-discovery,
#   project-genesis, scope-poc, template-update  — project-lifecycle, template-specific

# Reservoir skill names. These MUST match ~/.claude/skills/ exactly — a name that
# drifts out of the reservoir is a hard error below, not a warning (2026-07-19: 13
# pre-rename names sat here unnoticed after the code-/design-/workflow-/git- rename,
# so the template kept shipping stale copies while the renamed skills never synced).
SKILLS=(
  # git operations
  git-commit        # stage + commit
  git-pr            # stage + commit + PR

  # code quality
  code-pr           # review an open PR
  code-refactor     # quality-driven refactor
  code-review       # standing diff review (leveled 1/2/3)
  code-debug        # quick fix from error

  # workflow pipeline
  workflow-research # phase 1 — structured research artifact
  workflow-plan     # phase 2 — plan doc
  workflow-execute  # phase 3 — execute a plan phase
  workflow-review   # phase 4 — plan fidelity check
  workflow-refine   # batch refinement — backlog → trio triage → DoR gate → ready
  workflow-insights # usage analytics
  workflow-retro    # tooling retrospective + config audit

  # design / planning
  design-sprint     # full design sprint from scratch
  design-initiative # initiative → backlog
  design-milestones # initiative → phase checkpoints
  design-prototype  # spike/explore

  # cross-cutting
  akira             # interactive quality scanner (scan/wander/dao/all)
  docs-check        # structural drift detection (README/DESIGN.md vs codebase)
  github-projects   # Projects V2 GraphQL templates
  mcp-builder       # build MCP servers (Python FastMCP or Node SDK)
  new-agent         # scaffold a new subagent
  skill-creator     # skill CRUD + eval
  sanyi             # change contracts
)

# Fail fast on any name that no longer exists in the reservoir. Skipping with a
# warning lets a renamed skill rot in the template indefinitely — the warning
# scrolls past, the exit code stays 0, and stale copies keep shipping.
missing=()
for skill in "${SKILLS[@]}"; do
  skill="${skill%%[[:space:]]*}"  # strip inline comment
  [ -d "$RESERVOIR/$skill" ] || missing+=("skills/$skill")
done
for agent in "${AGENTS[@]}"; do
  agent_name="${agent%%[[:space:]]*}"  # strip inline comment if any
  [ -f "$AGENT_RESERVOIR/$agent_name.md" ] || missing+=("agents/$agent_name.md")
done
for rule in "${RULES[@]}"; do
  rule_name="${rule%%[[:space:]]*}"  # strip inline comment if any
  [ -f "$RULES_RESERVOIR/$rule_name" ] || missing+=("rules/$rule_name")
done
if [ ${#missing[@]} -gt 0 ]; then
  echo "error: ${#missing[@]} name(s) in SKILLS[]/AGENTS[]/RULES[] are not in the reservoir:" >&2
  printf '  %s\n' "${missing[@]}" >&2
  echo "Renamed? Update the array in this script. Retired? Remove it there and" >&2
  echo "git rm the stale template/.claude/ copy." >&2
  exit 1
fi

# Reverse check: a new reservoir skill added to ~/.claude/skills/ without
# updating SKILLS[] or DELIBERATELY_EXCLUDED[] would silently never ship.
# Warn (not fail) so a new skill upstream doesn't break an unrelated sync —
# but make it loud enough to act on. Mirrors sync-agent-references.sh:113–128.
unaccounted=()
while IFS= read -r dir; do
  name="$(basename "$dir")"
  in_skills=0
  for s in "${SKILLS[@]}"; do
    s="${s%%[[:space:]]*}"
    [ "$s" = "$name" ] && in_skills=1 && break
  done
  if [ "$in_skills" -eq 0 ]; then
    in_excluded=0
    for e in "${DELIBERATELY_EXCLUDED[@]}"; do
      e="${e%%[[:space:]]*}"
      [ "$e" = "$name" ] && in_excluded=1 && break
    done
    [ "$in_excluded" -eq 0 ] && unaccounted+=("$name")
  fi
done < <(find "$RESERVOIR" -maxdepth 1 -mindepth 1 -type d | sort)

if [ ${#unaccounted[@]} -gt 0 ]; then
  echo "warning: ${#unaccounted[@]} reservoir skill(s) are in neither SKILLS[] nor DELIBERATELY_EXCLUDED[]:" >&2
  printf '  %s\n' "${unaccounted[@]}" >&2
  echo "Add each to SKILLS[] (vendor it) or DELIBERATELY_EXCLUDED[] (document why not)." >&2
fi

# Every skill removed when global_skills_source=none must be one this script
# vendors in — otherwise the knob leaves orphans (2026-07-19: 15 renamed skills
# escaped cleanup because copier.yaml still listed pre-rename names). new-agent
# is exempt: include_agent_reference_library removes it in a separate task.
copier_yaml="$REPO_ROOT/copier.yaml"
EXEMPT=(new-agent)
if [ -f "$copier_yaml" ]; then
  unlisted=()
  while IFS= read -r name; do
    [ -z "$name" ] && continue
    exempt=0
    for e in "${EXEMPT[@]}"; do
      [ "$e" = "$name" ] && exempt=1 && break
    done
    [ "$exempt" -eq 1 ] && continue
    listed=0
    for skill in "${SKILLS[@]}"; do
      skill_name="${skill%%[[:space:]]*}"  # strip inline comment
      [ "$skill_name" = "$name" ] && listed=1 && break
    done
    [ "$listed" -eq 0 ] && unlisted+=("$name")
  done < <(grep -o "/\.claude/skills/[a-z-]*" "$copier_yaml" | sed 's|.*/||' | sort -u)

  for skill in "${SKILLS[@]}"; do
    skill="${skill%%[[:space:]]*}"  # strip inline comment
    grep -q "/\.claude/skills/$skill " "$copier_yaml" ||
      grep -q "/\.claude/skills/$skill'" "$copier_yaml" ||
      unlisted+=("$skill (vendored but never cleaned up)")
  done

  if [ ${#unlisted[@]} -gt 0 ]; then
    echo "warning: copier.yaml cleanup list and SKILLS[] disagree:" >&2
    printf '  %s\n' "${unlisted[@]}" >&2
    echo "Reconcile the global_skills_source == 'vendored' task in copier.yaml." >&2
  fi
fi

changed=()
for skill in "${SKILLS[@]}"; do
  skill="${skill%%[[:space:]]*}"  # strip inline comment
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

for agent in "${AGENTS[@]}"; do
  agent="${agent%%[[:space:]]*}"  # strip inline comment
  src="$AGENT_RESERVOIR/$agent.md"
  dst="$AGENT_TEMPLATE_ROOT/$agent.md"

  if ! diff -q "$src" "$dst" >/dev/null 2>&1; then
    changed+=("agents/$agent.md")
    if [ ! -f "$dst" ]; then
      echo "agents/$agent.md: new ($(wc -l < "$src" | tr -d ' ') lines)"
    else
      echo "agents/$agent.md:"
      { diff "$dst" "$src" 2>&1 || true; } | head -8 | sed 's/^/    /'
    fi
    if [ "$DRY_RUN" -eq 0 ]; then
      mkdir -p "$AGENT_TEMPLATE_ROOT"
      cp "$src" "$dst"
    fi
  fi
done

for rule in "${RULES[@]}"; do
  rule="${rule%%[[:space:]]*}"  # strip inline comment
  src="$RULES_RESERVOIR/$rule"
  dst="$RULES_TEMPLATE_ROOT/$rule"

  if ! diff -q "$src" "$dst" >/dev/null 2>&1; then
    changed+=("rules/$rule")
    if [ ! -f "$dst" ]; then
      echo "rules/$rule: new ($(wc -l < "$src" | tr -d ' ') lines)"
    else
      echo "rules/$rule:"
      { diff "$dst" "$src" 2>&1 || true; } | head -8 | sed 's/^/    /'
    fi
    if [ "$DRY_RUN" -eq 0 ]; then
      mkdir -p "$RULES_TEMPLATE_ROOT"
      cp "$src" "$dst"
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
