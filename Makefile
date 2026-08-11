include ~/.claude/Makefile.common

.PHONY: help lint test test_render new_project new_project_dev run_copier check_tools preview_defaults project

input_dir := .

help:  ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

lint:  ## Validate template paths, copier config, and Python lint
	@python3 scripts/validate_paths.py
	@ruff check scripts/

test:  ## Validate paths + catalog check
	@python3 scripts/validate_paths.py
	@python3 scripts/validate_paths.py --catalog-check

## Render the ML matrix entry to a real directory and run its pytest suite.
## validate_paths.py's run_render_tests() renders this same combination but only
## greps for unrendered Jinja before discarding the tree — the tests never run.
## Every ML step's Done-when command needs a rendered tree to run inside, so this
## target keeps the output and runs pytest in it.
## Usage: make test_render                 (renders to a temp dir, removes it after)
##        make test_render KEEP=1          (prints the path, leaves it in place)
##        make test_render DST=/some/path  (renders to a path you choose, keeps it)
##        make test_render PYTEST_ARGS="tests/unit/ml/test_transform.py -v"
##                                         (replaces the default pytest target)
test_render: check_tools
	@dst="$${DST:-$$(mktemp -d -t ait_render)}"; \
	keep="$${KEEP:-}"; [ -n "$${DST:-}" ] && keep=1; \
	echo "rendering to $$dst"; \
	copier copy --overwrite --defaults --trust \
	  -d project_name=TestProject -d scaffold_full_project=true \
	  -d primary_backend_language=python -d primary_chat_agent=lg_agent \
	  -d include_ml=true -d include_agent_reference_library=false \
	  -d global_skills_source=none -d enable_macos_notifications=false \
	  $(input_dir) "$$dst" >/dev/null || { echo "render FAILED"; rm -rf "$$dst"; exit 1; }; \
	( cd "$$dst" && uv sync --quiet && uv run pytest $${PYTEST_ARGS:-tests/unit/ml} ); \
	rc=$$?; \
	if [ -n "$$keep" ]; then echo "rendered tree kept at: $$dst"; else rm -rf "$$dst"; fi; \
	exit $$rc

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
