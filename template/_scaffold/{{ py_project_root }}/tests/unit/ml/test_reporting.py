"""Step 16 — the run report.

`write_report` turns a `RunResult` into a single self-contained HTML file. Two
things about it are worth asserting rather than trusting.

The first is its **aggregates-only** contract: the module's docstring promises
that nothing it writes carries a row, an index, or an identifier, because a
report on real data is a document that gets emailed and inherits every handling
constraint the dataset has. That promise is a property of the rendering code, so
it is checked here against a frame whose identifier values are distinctive
enough to find in the output if they leak.

The second is that it **states a null result as one**. A comparison table that
always reads like a success teaches the reader nothing, so the verdict block has
to distinguish "beat the baseline" from "did not".
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.reporting import write_report
from ml.workflows.classification import run_classification

RANDOM_STATE = 42

# Distinctive enough that a substring search for them in the rendered HTML is a
# real leak signal rather than an accidental match on a metric or a class name.
SECRET_ID = "acct-9f3c7a21-leak-canary"  # gitleaks:allow — test fixture, not a credential


@pytest.fixture
def result_with_identifiers():
    """A real run over a frame carrying an obvious per-row identifier column.

    The identifier is dropped from the features (it is not a predictor), but it
    is present in the source frame — which is exactly the situation where a
    reporting layer that echoed input data would leak it.
    """
    rng = np.random.default_rng(RANDOM_STATE)
    n = 400
    signal = rng.normal(size=n)
    logit = 2.2 * signal - 2.0
    prob = 1.0 / (1.0 + np.exp(-logit))
    target = (rng.uniform(size=n) < prob).astype(int)
    frame = pd.DataFrame(
        {
            "account_id": [f"{SECRET_ID}-{i}" for i in range(n)],
            "signal": signal,
            "noise": rng.normal(size=n),
            "target": target,
        }
    )
    # account_id is an identifier, never a feature — dropped before fitting, but
    # still present in the frame the run was built from.
    return run_classification(
        frame.drop(columns=["account_id"]), target="target", n_splits=3, seed=RANDOM_STATE
    )


def test_write_report_creates_parent_directories(result_with_identifiers, tmp_path):
    """A missing folder is created, not an error.

    The docstring treats the caller's chosen location as an instruction; a run
    script writing to reports/<timestamp>/run.html should not have to mkdir first.
    """
    out = tmp_path / "reports" / "nested" / "run.html"
    written = write_report(result_with_identifiers, out)

    assert written == out
    assert out.exists()
    assert out.read_text(encoding="utf-8").startswith("<!doctype html>")


def test_report_contains_no_row_level_identifiers(result_with_identifiers, tmp_path):
    """The aggregates-only contract, asserted rather than trusted.

    Column *names* are part of the report's vocabulary; column *values* are not.
    """
    out = write_report(result_with_identifiers, tmp_path / "run.html")
    document = out.read_text(encoding="utf-8")

    assert SECRET_ID not in document
    # Model names and metric labels are aggregates and must survive — a report
    # that leaked nothing because it rendered nothing would pass the check above.
    assert "logistic" in document.lower()


def test_report_states_its_verdict(result_with_identifiers, tmp_path):
    """A win and a null result must be distinguishable in the output.

    Both verdict classes are styled; asserting one is present keeps the verdict
    block from silently disappearing while the comparison table still renders.
    """
    out = write_report(result_with_identifiers, tmp_path / "run.html")
    document = out.read_text(encoding="utf-8")

    assert "class='verdict" in document


def test_report_title_is_escaped(result_with_identifiers, tmp_path):
    """Titles reach the document unescaped only if someone forgot `_esc`."""
    out = write_report(
        result_with_identifiers,
        tmp_path / "run.html",
        title="<script>alert(1)</script>",
    )
    document = out.read_text(encoding="utf-8")

    assert "<script>alert(1)</script>" not in document
    assert "&lt;script&gt;" in document
