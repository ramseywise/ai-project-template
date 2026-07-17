from __future__ import annotations

from pathlib import Path

import pytest

from core.index import build_index
from core.ingestion import load_raw_articles
from core.preprocessing import clean_and_dedupe, write_jsonl

# pytest runs from the project root (pythonpath includes "." in pyproject.toml),
# so this is the same relative path `make corpus-ingest` uses in a real project.
CORPUS_DIR = Path("data/corpus")


@pytest.fixture
def corpus_dir() -> Path:
    """Path to the real example corpus shipped with the project."""
    return CORPUS_DIR


@pytest.fixture
def indexed_db(tmp_path: Path) -> str:
    """Build a real DuckDB FTS index from the example corpus into a temp file.

    Chains the same pipeline `make corpus-ingest` would run: load raw articles,
    clean/dedupe them, write the intermediate JSONL, then build the FTS index.
    Returns the path to the resulting DuckDB file.
    """
    articles = load_raw_articles(CORPUS_DIR)
    cleaned = clean_and_dedupe(articles)

    jsonl_path = tmp_path / "articles.jsonl"
    write_jsonl(cleaned, jsonl_path)

    db_path = str(tmp_path / "index.duckdb")
    build_index(jsonl_path, db_path)
    return db_path
