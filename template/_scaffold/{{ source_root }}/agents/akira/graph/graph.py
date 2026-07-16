"""Akira graph design — routes mode to the correct subgraph node.

Modes:
  kiyoko → yin wander: reads delta, surfaces questions in stdout
  kaneda → yang scan:  5 parallel domain subagents, writes findings doc + JSON
  dao    → the path:   triages findings, applies, test-gated, writes summary
"""

from __future__ import annotations

from typing import Literal

from langgraph.graph import END, START, StateGraph

from agents.akira.graph.state import AkiraState


def _route(state: AkiraState) -> Literal["kiyoko", "kaneda", "dao"]:
    return state["mode"].value  # type: ignore[return-value]


def design():
    from agents.akira.graph.nodes.dao import dao_node
    from agents.akira.graph.nodes.kaneda import kaneda_node
    from agents.akira.graph.nodes.kiyoko import kiyoko_node

    graph = StateGraph(AkiraState)

    graph.add_node("kiyoko", kiyoko_node)
    graph.add_node("kaneda", kaneda_node)
    graph.add_node("dao", dao_node)

    graph.add_conditional_edges(START, _route, ["kiyoko", "kaneda", "dao"])
    graph.add_edge("kiyoko", END)
    graph.add_edge("kaneda", END)
    graph.add_edge("dao", END)

    return graph.compile()
