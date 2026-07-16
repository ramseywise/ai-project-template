from __future__ import annotations

from agents.lg_agent.schema import Source
from agents.lg_agent.settings import settings
from agents.lg_agent.state import State
from core.index import search


def retrieve_node(state: State) -> dict:
    results = search(settings.vectordb_path, state["message"], k=settings.retrieval_top_k)
    sources = [Source(id=r.id, title=r.title, score=r.score) for r in results]
    context_snippets = [f"# {r.title}\n{r.text}" for r in results]
    return {"sources": sources, "context_snippets": context_snippets}
