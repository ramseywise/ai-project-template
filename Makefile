.PHONY: new_project new_project_dev run_copier check_tools preview_defaults project

input_dir := .

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
