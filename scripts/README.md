# scripts/ — template-maintainer utilities

Tools for working on the template itself. Nothing here ships into rendered
projects (only `template/` is rendered).

| Script | What it does |
|---|---|
| `preview_defaults.py` | Evaluates `copier.yaml`'s Jinja default expressions for a given set of answers without rendering — quick way to check what a config would derive (`scaffold_full_project`, `include_*` toggles, directory names) before running a real render. |
| `sync-global-skills.sh` | Copies the shared workflow skills from the `~/.claude/skills/` reservoir into `template/.claude/skills/` (the template's vendored snapshot). Run before rendering/releasing so clones get the latest reservoir state; see `global_skills_source` in `copier.yaml`. |
| `sync-agent-references.sh` | Copies agent framework references from the canonical source into `template/.agents/`. Same reservoir→template pattern as `sync-global-skills.sh`. |
