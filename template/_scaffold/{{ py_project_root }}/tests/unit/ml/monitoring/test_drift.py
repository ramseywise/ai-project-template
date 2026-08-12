"""Monitoring stage — drift and train/serve skew.

The load-bearing claims:

1. PSI bins on *reference* quantiles, not the combined sample. Binning on the
   combination lets the current window move the bin edges and mask the shift
   being measured — the metric would then be least sensitive exactly when it
   matters most.
2. A stable population scores near zero and a shifted one scores above the
   conventional 0.25 band, so the returned number is interpretable rather than
   merely ordinal.
3. Train/serve skew is detected per row, not in aggregate.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.monitoring import (
    PSI_SIGNIFICANT,
    detect_drift,
    ks_statistic,
    population_stability_index,
    train_serve_skew,
)

SEED = 42


@pytest.fixture
def reference():
    rng = np.random.default_rng(SEED)
    return pd.DataFrame(
        {"score": rng.normal(0, 1, 1000), "tier": rng.choice(["a", "b", "c"], 1000)}
    )


def test_psi_is_near_zero_for_the_same_distribution(reference):
    rng = np.random.default_rng(SEED + 1)
    current = pd.Series(rng.normal(0, 1, 1000))

    psi = population_stability_index(reference["score"], current)

    assert psi < 0.1, f"an unshifted population should score below the noise band, got {psi}"


def test_psi_flags_a_real_shift(reference):
    shifted = pd.Series(np.random.default_rng(SEED).normal(2, 1, 1000))

    psi = population_stability_index(reference["score"], shifted)

    assert psi > PSI_SIGNIFICANT, f"a 2-sigma shift should exceed the 0.25 band, got {psi}"


def test_psi_bins_on_the_reference_not_the_combination():
    """The subtle correctness property, tested by asymmetry.

    Quantile edges taken from the reference make PSI(a, b) and PSI(b, a) differ.
    If the implementation binned on the combined sample the two would coincide —
    and the metric would be blind to exactly the shift it is asked to find.
    """
    rng = np.random.default_rng(SEED)
    narrow = pd.Series(rng.normal(0, 1, 500))
    wide = pd.Series(rng.normal(0, 5, 500))

    forward = population_stability_index(narrow, wide)
    backward = population_stability_index(wide, narrow)

    assert not np.isclose(forward, backward, rtol=0.05), (
        "PSI was symmetric, which means the bins were not cut on the reference"
    )


def test_psi_handles_categorical_columns(reference):
    skewed = pd.Series(["a"] * 900 + ["b"] * 50 + ["c"] * 50)

    psi = population_stability_index(reference["tier"], skewed)

    assert psi > 0, "a categorical shift must register"
    assert np.isfinite(psi), "empty bins must not produce inf via log(0)"


def test_psi_is_finite_when_a_category_disappears(reference):
    """log(0) is the obvious way this metric breaks; the epsilon floor prevents it."""
    collapsed = pd.Series(["a"] * 1000)

    psi = population_stability_index(reference["tier"], collapsed)

    assert np.isfinite(psi)


def test_empty_input_scores_zero_rather_than_raising(reference):
    assert population_stability_index(reference["score"], pd.Series([], dtype=float)) == 0.0
    assert ks_statistic(reference["score"], pd.Series([], dtype=float)) == 0.0


def test_detect_drift_only_compares_shared_columns(reference):
    """A column present on one side only is a schema change for ingest/, not drift."""
    current = reference.drop(columns=["tier"]).assign(brand_new=1.0)

    report = detect_drift(reference, current)

    assert {f.feature for f in report.features} == {"score"}
    assert report.reference_rows == len(reference)


def test_detect_drift_marks_the_drifted_features(reference):
    current = reference.assign(score=reference["score"] + 5)

    report = detect_drift(reference, current)

    assert "score" in report.drifted_features


def test_ks_returns_zero_for_non_numeric(reference):
    assert ks_statistic(reference["tier"], reference["tier"]) == 0.0


# ── train/serve skew ─────────────────────────────────────────────────────────


def test_identical_rows_have_no_skew():
    row = {"amount": 10.0, "ratio": 0.5}
    assert train_serve_skew(row, dict(row)) == {}


def test_a_differing_value_is_reported():
    skew = train_serve_skew({"amount": 10.0}, {"amount": 10.5})
    assert "amount" in skew
    assert "10.0" in skew["amount"] and "10.5" in skew["amount"]


def test_a_feature_missing_from_one_side_is_reported():
    skew = train_serve_skew({"only_train": 1.0}, {"only_serve": 1.0})
    assert skew["only_train"] == "computed at training time only"
    assert skew["only_serve"] == "computed at serving time only"


def test_tolerance_absorbs_float_noise():
    """Float noise from a different summation order is not a skew bug; a real
    difference in the computation is."""
    assert train_serve_skew({"x": 1.0}, {"x": 1.0 + 1e-9}) == {}
    assert train_serve_skew({"x": 1.0}, {"x": 1.01}) != {}
