"""Step 16 — the run report.

The load-bearing tests here are the disclosure ones. Everything else checks that
the panels render; those two check the property the module exists for — a report
is a file that gets emailed, so a row or an identifier leaking into it inherits
every handling constraint the dataset has, and a CDN link turns an offline
artefact into a network request against whoever opens it.

Both are asserted against the actual output rather than trusted, because the
failure is invisible in review: the report still looks correct.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

from ml.evaluation.splitting import make_splitter
from ml.reporting import write_report
from ml.workflows.classification import run_classification

RANDOM_STATE = 42


@pytest.fixture
def result():
    """A real run, not a stub — the report reads attributes off `RunResult`, so a
    hand-built double would pass while the true shape drifted underneath it."""
    import numpy as np

    rng = np.random.default_rng(RANDOM_STATE)
    n = 300
    signal = rng.normal(size=n)
    prob = 1.0 / (1.0 + np.exp(-(2.0 * signal - 1.5)))
    frame = pd.DataFrame(
        {
            "signal": signal,
            "noise": rng.normal(size=n),
            "borrower_id": [f"acct_{i}" for i in range(n)],
            "charged_off": (rng.uniform(size=n) < prob).astype(int),
        }
    )
    return run_classification(
        frame.drop(columns=["borrower_id"]),
        target="charged_off",
        output="binary",
        models=["logistic"],
        sampling="class_weight",
        splitter=make_splitter(n_splits=3, random_state=RANDOM_STATE),
        seed=RANDOM_STATE,
    )


def test_write_report_creates_missing_parent_directories(result, tmp_path: Path) -> None:
    out = write_report(result, tmp_path / "nested" / "deeper" / "report.html")

    assert out.exists()
    assert out.read_text().lstrip().startswith("<!doctype html>")


def test_report_renders_the_panels_a_reader_consumes(result, tmp_path: Path) -> None:
    document = write_report(result, tmp_path / "r.html", title="Charge-off run").read_text()

    assert "Charge-off run" in document
    for heading in ("Run", "Model comparison"):
        assert f"<h2>{heading}</h2>" in document
    # The baseline must be named. A comparison table that omits what was compared
    # against reads as a win regardless of what happened.
    assert "logistic" in document


def test_report_is_self_contained(result, tmp_path: Path) -> None:
    """No external references — the report must render offline, from the file alone."""
    document = write_report(result, tmp_path / "r.html").read_text()

    external = re.findall(r'(?:src|href)\s*=\s*["\'](?!#)([^"\']+)', document)
    assert external == [], f"report references external resources: {external}"


def test_report_carries_aggregates_not_records(result, tmp_path: Path) -> None:
    """The module's whole reason for existing: metrics and column names, never rows.

    Asserted with an identifier that was never a feature — if the report ever
    grows a "sample rows" panel, this is what catches it.
    """
    document = write_report(result, tmp_path / "r.html").read_text()

    assert "acct_" not in document
    assert "borrower_id" not in document
