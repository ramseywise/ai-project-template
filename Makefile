.PHONY: help lint test new_project new_project_dev run_copier check_tools preview_defaults project pull status push quick-pr ship

input_dir := .

help:  ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

lint:  ## Validate template paths and copier config
	@python3 scripts/validate_paths.py

test:  ## Validate paths + catalog check
	@python3 scripts/validate_paths.py
	@python3 scripts/validate_paths.py --catalog-check

pull:  ## Pull latest from origin/main
	git pull origin main

status:  ## Show branch, unpushed commits, staged changes, open PRs
	@echo "=== ai-project-template ==="
	@echo "Branch: $$(git branch --show-current)"
	@echo "Unpushed:"
	@git log origin/$$(git branch --show-current)..HEAD --oneline 2>/dev/null || echo "  (no remote tracking)"
	@echo "Staged:"
	@git diff --cached --stat 2>/dev/null || true
	@echo "Modified:"
	@git diff --stat 2>/dev/null || true
	@echo "Open PRs:"
	@gh pr list --state open --json number,title,headBranch --jq '.[] | "#\(.number) \(.title) [\(.headBranch)]"' 2>/dev/null || echo "  (none)"

push:  ## Push current branch to origin
	git push -u origin $$(git branch --show-current)

quick-pr:  ## Create PR from current branch with auto-generated body
	@BRANCH=$$(git branch --show-current); \
	if [ "$$BRANCH" = "main" ]; then echo "Error: can't PR from main"; exit 1; fi; \
	EXISTING=$$(gh pr list --head "$$BRANCH" --json number --jq '.[0].number' 2>/dev/null); \
	if [ -n "$$EXISTING" ]; then echo "PR #$$EXISTING already exists for $$BRANCH"; exit 0; fi; \
	COMMITS=$$(git log origin/main..HEAD --oneline 2>/dev/null); \
	ISSUES=$$(echo "$$COMMITS" | grep -oE '#[0-9]+' | sort -u | tr '\n' ' ' | xargs); \
	BODY=$$(printf "## Summary\n%s\n\n%s\n" "$$COMMITS" "$${ISSUES:+(no issue references found)}"); \
	echo "Creating PR for $$BRANCH..."; \
	gh pr create --title "$$BRANCH" --body "$$BODY"

ship: lint test pull push quick-pr  ## lint → test → pull → push → PR

check_tools:
	@command -v copier >/dev/null 2>&1 || { echo "copier not found — install with: uv tool install copier"; exit 1; }

## Apply this template into a new or existing project directory.
## Usage: make new_project output_dir="~/Workspace/my-project" project_name="My Project"
new_project: check_tools
	@$(MAKE) run_copier VCS_REF=""

## Same as new_project, but renders from the current dirty working tree
## instead of requiring a committed ref — useful while iterating on the template itself.
new_project_dev: check_tools
	@$(MAKE) run_copier VCS_REF="--vcs-ref HEAD"

run_copier:
	@output_dir=$${output_dir:-$$(read -p "output_dir (existing or new project path): " r && echo $$r)}; \
	project_name=$${project_name:-$$(read -p "project_name: " r && echo $$r)}; \
	mkdir -p "$$output_dir"; \
	output_dir=$$(cd "$$output_dir" && pwd); \
	copier copy $(VCS_REF) $(input_dir) "$$output_dir" --trust -d "project_name_input=$$project_name"

## Render a project from a genesis answers file produced by /project-genesis.
## Usage: make project ANSWERS=/tmp/genesis-answers.yml output_dir=~/workspace/my-project
##        make project ANSWERS=/tmp/genesis-answers.yml output_dir=~/workspace/my-project OVERWRITE=1
project: check_tools
	@answers=$${ANSWERS:-}; \
	if [ -z "$$answers" ]; then echo "ANSWERS is required — e.g. make project ANSWERS=/tmp/genesis-answers.yml output_dir=..."; exit 1; fi; \
	output_dir=$${output_dir:-$$(read -p "output_dir (target project path): " r && echo $$r)}; \
	mkdir -p "$$output_dir"; \
	output_dir=$$(cd "$$output_dir" && pwd); \
	overwrite_flag=$$([ -n "$${OVERWRITE}" ] && echo "--overwrite" || echo ""); \
	copier copy --vcs-ref HEAD --trust --defaults $$overwrite_flag --data-file "$$answers" $(input_dir) "$$output_dir"

## Preview resolved copier defaults without rendering any files.
## Usage: make preview_defaults project_type=rag external_systems="[slack,github]"
##        make preview_defaults ARGS="--all"
preview_defaults:
	@python3 scripts/preview_defaults.py $(filter-out $@,$(MAKECMDGOALS)) $(ARGS)
