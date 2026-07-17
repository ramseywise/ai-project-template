#!/usr/bin/env bash
# Idempotent project bootstrap — safe to re-run.
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found — install it: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 1
fi

if [ ! -d .git ]; then
  git init
  echo "Initialized a new git repository."
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example — fill in your API keys before running the agent."
fi

echo "Syncing dependencies with uv..."
uv sync --group dev --group notebooks

mkdir -p data/processed data/stores

echo "Done. Next steps:"
echo "  1. Edit .env with your ANTHROPIC_API_KEY"
echo "  2. make rag-corpus-ingest  # build rag_agent's embedding index from data/corpus/"
echo "  3. make rag-up             # start the rag_agent retrieval service"
echo "  4. make rag-chat           # smoke-test it"
