"""Embeds the same preprocessed corpus core/ingestion.py produces for lg_agent's
FTS index, and stores it in rag_agent's own vector store (backend chosen by
settings.vector_backend) — same source articles, two different retrieval
mechanisms side by side."""

from __future__ import annotations

import json
from pathlib import Path

from agents.rag_agent.vectorstore import get_vector_index


def build_index(jsonl_path: Path) -> int:
    lines = jsonl_path.read_text(encoding="utf-8").splitlines()
    rows = [json.loads(line) for line in lines if line]
    index = get_vector_index()
    index.upsert([(row["id"], row["title"], row["text"]) for row in rows])
    return len(rows)
