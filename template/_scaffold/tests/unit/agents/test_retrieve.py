from __future__ import annotations

from agents.lg_agent.nodes.retrieve import retrieve_node


def test_retrieve_node_populates_sources_and_snippets(wired_vectordb: str) -> None:
    result = retrieve_node({"message": "How do I descale the machine?"})

    assert "sources" in result
    assert "context_snippets" in result
    assert len(result["sources"]) > 0
    assert len(result["context_snippets"]) == len(result["sources"])

    top_source = result["sources"][0]
    assert top_source.id == "descaling"
    assert top_source.title
    assert top_source.score > 0


def test_retrieve_node_context_snippets_include_title_and_text(wired_vectordb: str) -> None:
    result = retrieve_node({"message": "warranty coverage"})

    assert len(result["context_snippets"]) > 0
    snippet = result["context_snippets"][0]
    assert snippet.startswith("# ")


def test_retrieve_node_returns_empty_for_nonsense_query(wired_vectordb: str) -> None:
    result = retrieve_node({"message": "zzzqqqxxx_no_such_term_exists"})

    assert result["sources"] == []
    assert result["context_snippets"] == []
