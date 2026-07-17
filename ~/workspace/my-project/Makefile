.PHONY: setup corpus-preprocess \
        rag-corpus-ingest rag-up rag-down rag-wait rag-chat \
        eval-heuristic eval-gate eval-render \
        nbks-corpus test test-smoke test-integration \
        lint lint-check typecheck \
        docker-up docker-down

# src/ holds "agents" (imported bare, e.g. `agents.lg_agent`); "core"
# and "evals" live at the project root — both need to be on PYTHONPATH
# for anything invoked outside of pytest (which reads pythonpath from pyproject.toml).
PY := PYTHONPATH=src:. uv run python
UVICORN := PYTHONPATH=src:. uv run uvicorn

setup:
	./project_init.sh

# --- Corpus pipeline (core/) ---
corpus-preprocess:
	$(PY) -m core preprocess

# --- Example agent (src/agents/rag_agent) — same corpus, embedding-based retrieval ---
rag-corpus-ingest: corpus-preprocess
	$(PY) -m core rag-ingest

rag-up:
	$(UVICORN) agents.rag_agent.main:app --port $${RAG_PORT:-8011} --reload &

rag-down:
	pkill -f "uvicorn agents.rag_agent.main:app" 2>/dev/null || true

rag-wait:
	@for i in $$(seq 1 30); do \
		curl -sf http://localhost:$${RAG_PORT:-8011}/health >/dev/null && echo "rag_agent is up" && exit 0; \
		sleep 1; \
	done; \
	echo "rag_agent did not become healthy in time" >&2; exit 1

rag-chat:
	curl -s -X POST http://localhost:$${RAG_PORT:-8011}/chat \
		-H "Content-Type: application/json" \
		-d '{"message": "How do I descale the machine?", "thread_id": "smoke-test"}' | uv run python -m json.tool

# --- Evals (evals/) ---
eval-heuristic:
	$(PY) -m evals.pipelines.run heuristic

# Same run, but exits non-zero when any evals/targets.yaml metric is
# below target — the CI-able form of DESIGN.md's Evaluation table.
eval-gate:
	$(PY) -m evals.pipelines.run heuristic --gate

eval-render:
	$(PY) -m evals.pipelines.run render

# --- Notebooks (nbks/, Marimo) ---
nbks-corpus:
	PYTHONPATH=src:. uv run marimo run nbks/corpus_analysis.py

# --- Tests ---
test:
	uv run pytest tests/unit -q

test-smoke:
	uv run pytest tests/smoke -q

test-integration:
	uv run pytest tests/integration -q -m integration

# --- Lint / typecheck ---
# Scoped to this project's own source, not the whole repo root — .claude/.agents/
# ship vendored reference material (e.g. mcp-builder's example scripts) that
# isn't held to this project's lint config and was never meant to be.
LINT_PATHS := src core evals tests

lint:
	uv run ruff check $(LINT_PATHS) --fix
	uv run ruff format $(LINT_PATHS)

lint-check:
	uv run ruff check $(LINT_PATHS)
	uv run ruff format --check $(LINT_PATHS)

typecheck:
	uv run pyright

# --- Docker (infrastructure/containers) ---
docker-up:
	docker compose -f infrastructure/containers/docker-compose.yml up --build

docker-down:
	docker compose -f infrastructure/containers/docker-compose.yml down
