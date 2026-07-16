from __future__ import annotations

import pytest

from agents.lg_agent.settings import settings


@pytest.fixture
def wired_vectordb(indexed_db: str, monkeypatch: pytest.MonkeyPatch) -> str:
    """Point the lg_agent settings singleton at the real temp index.

    Lets retrieval-dependent tests (nodes.retrieve, main /chat) hit real data
    without requiring `make corpus-ingest` to have been run against the
    project's default `data/stores/vectordb.duckdb` first. lg_agent-specific
    (unlike ``indexed_db``/``corpus_dir`` in the root conftest, which test
    core/index.py's generic BM25 mechanics) — lives here so it's removed
    automatically alongside ``tests/unit/agents/`` when lg_agent isn't scaffolded.
    """
    monkeypatch.setattr(settings, "vectordb_path", indexed_db)
    return indexed_db
