"""Evaluation stage — metrics.

Two claims are load-bearing here and each gets a test that could fail:

1. PR-AUC is the headline under imbalance, and it is a *different* number from
   ROC-AUC — demonstrated on a frame where ROC looks good and precision is poor.
2. Clustering metrics degrade honestly (None, not a fabricated score) when the
   input cannot support them.

Calibration and threshold tests moved to `../calibration/test_calibration.py`
when those modules became their own stage — the split is the point, so the tests
follow the code rather than staying in one file.
"""

from __future__ import annotations

import numpy as np
import pytest
from sklearn.datasets import make_blobs, make_classification
from sklearn.linear_model import LogisticRegression

from ml.evaluation.metrics import (
    classification_metrics,
    clustering_metrics,
    pr_curve,
    precision_at_k,
    regression_metrics,
    roc_curve_points,
)

RANDOM_STATE = 42


@pytest.fixture
def imbalanced_predictions():
    """A 95/5 frame with a model that ranks decently but is not sharp.

    Constructed so ROC-AUC flatters and average precision does not — the whole
    argument for leading with PR-AUC.
    """
    rng = np.random.default_rng(RANDOM_STATE)
    n = 1000
    y_true = (rng.random(n) < 0.05).astype(int)
    # Positives score higher on average, but the distributions overlap heavily.
    y_prob = np.clip(
        np.where(y_true == 1, rng.normal(0.55, 0.2, n), rng.normal(0.30, 0.2, n)),
        0.001,
        0.999,
    )
    return y_true, y_prob


# ── metrics ──────────────────────────────────────────────────────────────────


def test_pr_auc_is_the_headline_and_is_lower_than_roc_auc(imbalanced_predictions):
    """The claim in the module docstring, stated as an assertion.

    ROC-AUC divides false positives by the majority-class count, so it stays
    high while the precision an operator experiences is poor. If these two ever
    converge on a 95/5 frame, the fixture stopped being imbalanced.
    """
    y_true, y_prob = imbalanced_predictions
    metrics = classification_metrics(y_true, (y_prob >= 0.5).astype(int), y_prob)

    name, value = metrics.headline(imbalanced=True)
    assert name == "average_precision"
    assert value == metrics.average_precision

    assert metrics.roc_auc > metrics.average_precision, (
        "on a 95/5 frame ROC-AUC should flatter relative to PR-AUC; "
        f"got roc_auc={metrics.roc_auc:.3f} ap={metrics.average_precision:.3f}"
    )
    assert metrics.prevalence == pytest.approx(np.mean(y_true))


def test_headline_falls_back_to_roc_when_not_imbalanced(imbalanced_predictions):
    y_true, y_prob = imbalanced_predictions
    metrics = classification_metrics(y_true, (y_prob >= 0.5).astype(int), y_prob)
    name, _ = metrics.headline(imbalanced=False)
    assert name == "roc_auc"


def test_probability_metrics_are_none_without_probabilities(imbalanced_predictions):
    """Missing must not look like zero — a report that prints 0.00 for a metric
    that was never computed is worse than one that prints nothing."""
    y_true, y_prob = imbalanced_predictions
    metrics = classification_metrics(y_true, (y_prob >= 0.5).astype(int))

    assert metrics.average_precision is None
    assert metrics.roc_auc is None
    assert metrics.brier is None
    assert metrics.accuracy > 0


def test_precision_at_k_is_the_fixed_capacity_number(imbalanced_predictions):
    """Top-50 precision must beat the base rate for a model that ranks at all,
    and must beat top-500 precision, since the ranking degrades as k grows."""
    y_true, y_prob = imbalanced_predictions
    at_50 = precision_at_k(y_true, y_prob, 50)
    at_500 = precision_at_k(y_true, y_prob, 500)

    assert at_50 > np.mean(y_true), "a ranking model should beat the base rate at the top"
    assert at_50 >= at_500


def test_precision_at_k_clamps_above_the_row_count(imbalanced_predictions):
    y_true, y_prob = imbalanced_predictions
    assert precision_at_k(y_true, y_prob, 10_000) == pytest.approx(np.mean(y_true))


def test_precision_at_k_rejects_non_positive_k(imbalanced_predictions):
    y_true, y_prob = imbalanced_predictions
    with pytest.raises(ValueError, match="positive"):
        precision_at_k(y_true, y_prob, 0)


def test_pr_curve_baseline_is_prevalence_and_roc_baseline_is_half(imbalanced_predictions):
    """The no-skill reference differs between the two curves; a report that drew
    0.5 on a PR chart would be drawing a line no model is measured against."""
    y_true, y_prob = imbalanced_predictions

    pr = pr_curve(y_true, y_prob)
    roc = roc_curve_points(y_true, y_prob)

    assert pr.baseline == pytest.approx(np.mean(y_true))
    assert roc.baseline == 0.5
    assert len(pr.x) == len(pr.y) and len(pr.x) > 1
    assert len(roc.x) == len(roc.y) and len(roc.x) > 1


def test_multiclass_metrics_include_per_class_breakdown():
    x, y = make_classification(
        n_samples=300,
        n_features=8,
        n_informative=5,
        n_classes=3,
        random_state=RANDOM_STATE,
    )
    model = LogisticRegression(max_iter=1000, random_state=RANDOM_STATE).fit(x, y)
    metrics = classification_metrics(y, model.predict(x), model.predict_proba(x))

    assert set(metrics.per_class) == {"0", "1", "2"}
    assert metrics.roc_auc is not None, "multiclass ROC-AUC is one-vs-rest macro"
    assert metrics.average_precision is None, "average precision is binary-only here"
    assert len(metrics.confusion) == 3


def test_regression_mape_is_none_when_a_true_value_is_zero():
    """Dividing by zero would produce an infinity that poisons the mean silently."""
    with_zero = regression_metrics([0.0, 1.0, 2.0], [0.1, 1.1, 1.9])
    without_zero = regression_metrics([1.0, 2.0, 3.0], [1.1, 1.9, 3.2])

    assert with_zero.mape is None
    assert without_zero.mape is not None and without_zero.mape > 0
    assert with_zero.rmse > 0


def test_clustering_metrics_exclude_dbscan_noise_from_scores():
    """Noise rows belong to no cluster, so scoring them is meaningless — but the
    count must survive, because "most of the frame was noise" is the diagnostic."""
    x, y = make_blobs(n_samples=150, centers=3, random_state=RANDOM_STATE)
    labels = y.copy()
    labels[:20] = -1  # mark 20 rows as noise, the DBSCAN convention

    metrics = clustering_metrics(x, labels)

    assert metrics.n_noise == 20
    assert metrics.n_clusters == 3, "noise is not a cluster"
    assert "-1" not in metrics.cluster_sizes
    assert metrics.silhouette is not None and metrics.silhouette > 0


def test_clustering_metrics_degrade_to_none_with_a_single_cluster():
    x, _ = make_blobs(n_samples=50, centers=1, random_state=RANDOM_STATE)
    metrics = clustering_metrics(x, np.zeros(50, dtype=int))

    assert metrics.n_clusters == 1
    assert metrics.silhouette is None, "silhouette is undefined for one cluster"
