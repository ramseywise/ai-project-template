"""Akira CLI.

Usage:
    python -m agents.akira              # kaneda: full scan
    python -m agents.akira kiyoko       # yin: perceive, surface questions
    python -m agents.akira dao          # the path: triage findings, apply + test
    python -m agents.akira [path]       # kaneda scoped to path
"""

from __future__ import annotations

import argparse

from agents.akira.graph.graph import design
from agents.akira.schema import AkiraMode


def main() -> None:
    parser = argparse.ArgumentParser(prog="akira", description="Akira — codebase quality agent")
    parser.add_argument(
        "mode_or_path",
        nargs="?",
        default=None,
        help="wander | fix | <path> (default: full kaneda scan)",
    )
    args = parser.parse_args()

    arg = args.mode_or_path
    if arg in ("kiyoko", "wander", "?"):
        mode, path = AkiraMode.kiyoko, None
    elif arg in ("dao", "fix"):
        mode, path = AkiraMode.dao, None
    elif arg in ("kaneda", "scan", None):
        mode, path = AkiraMode.kaneda, None
    else:
        mode, path = AkiraMode.kaneda, arg

    graph = design()
    graph.invoke(
        {
            "mode": mode,
            "path": path,
            "git_context": None,
            "questions": [],
            "findings": [],
            "error": None,
        }
    )


if __name__ == "__main__":
    main()
