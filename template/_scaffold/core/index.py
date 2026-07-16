from __future__ import annotations

import json
from pathlib import Path

import duckdb

from core.models import SearchResult


def build_index(jsonl_path: Path, db_path: str) -> None:
    """Build a DuckDB full-text-search index from a preprocessed JSONL corpus.

    ``db_path`` may be a filesystem path or ``:memory:``.
    """
    rows = [
        json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines() if line
    ]

    con = duckdb.connect(db_path)
    con.execute("INSTALL fts")
    con.execute("LOAD fts")
    con.execute("DROP TABLE IF EXISTS articles")
    con.execute("CREATE TABLE articles (id VARCHAR, title VARCHAR, text VARCHAR, category VARCHAR)")
    con.executemany(
        "INSERT INTO articles VALUES (?, ?, ?, ?)",
        [(row["id"], row["title"], row["text"], row["category"]) for row in rows],
    )
    con.execute("PRAGMA create_fts_index('articles', 'id', 'title', 'text', overwrite=1)")
    con.close()


def search(db_path: str, query: str, k: int = 5) -> list[SearchResult]:
    """BM25 search over the ``articles`` FTS index. Returns up to ``k`` results,
    best match first. Empty list if the index has no match for ``query``."""
    con = duckdb.connect(db_path)
    con.execute("INSTALL fts")
    con.execute("LOAD fts")
    rows = con.execute(
        """
        SELECT id, title, text, score
        FROM (
            SELECT id, title, text, fts_main_articles.match_bm25(id, ?) AS score
            FROM articles
        )
        WHERE score IS NOT NULL
        ORDER BY score DESC
        LIMIT ?
        """,
        [query, k],
    ).fetchall()
    con.close()
    return [SearchResult(id=row[0], title=row[1], text=row[2], score=row[3]) for row in rows]
