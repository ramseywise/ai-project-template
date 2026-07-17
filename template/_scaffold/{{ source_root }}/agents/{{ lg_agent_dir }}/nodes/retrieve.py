from __future__ import annotations

from core.index import search

from ..schema import Source
from ..settings import settings
from ..state import State


def retrieve_node(state: State) -> dict:
    results = search(settings.vectordb_path, state["message"], k=settings.retrieval_top_k)
    sources = [Source(id=r.id, title=r.title, score=r.score) for r in results]
    context_snippets = [f"# {r.title}\n{r.text}" for r in results]
    return {"sources": sources, "context_snippets": context_snippets}
