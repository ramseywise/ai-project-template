"""Drift and train/serve skew — the last stage, and the only one that runs after
a model is already making decisions.

PSI (population stability index) is the default because it is the metric credit
and risk teams already read, it works on both numeric and categorical columns
once binned, and its conventional bands (0.1 / 0.25) are widely agreed. The
Kolmogorov-Smirnov statistic is offered for numeric columns where a
distribution-shape difference matters more than a bin-mass difference.

Train/serve skew is checked separately from drift and is a different bug: drift
means the world changed, skew means the two code paths disagree about the same
world. Skew is the more dangerous of the two because a model can look healthy on
every offline metric while being fed differently-computed features in production.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ml.schemas import DriftReport, FeatureDrift

PSI_MODERATE = 0.1
"""Conventional band: below this is noise."""
PSI_SIGNIFICANT = 0.25
"""Conventional band: above this is a material population shift."""

_EPSILON = 1e-6
"""Floor for empty bins — PSI's log ratio is undefined at zero."""


def population_stability_index(
    reference: pd.Series,
    current: pd.Series,
    n_bins: int = 10,
) -> float:
    """PSI between two samples of one feature.

    Bins are cut on the *reference* quantiles, never on the combined sample:
    binning on the combination lets the current window move the bin edges and
    hide the very shift being measured.
    """
    reference = reference.dropna()
    current = current.dropna()
    if reference.empty or current.empty:
        return 0.0

    if pd.api.types.is_numeric_dtype(reference) and reference.nunique() > n_bins:
        edges = np.unique(np.quantile(reference, np.linspace(0, 1, n_bins + 1)))
        edges[0], edges[-1] = -np.inf, np.inf
        ref_counts = np.histogram(reference, bins=edges)[0]
        cur_counts = np.histogram(current, bins=edges)[0]
    else:
        categories = reference.astype(str).value_counts().index
        ref_counts = np.array([(reference.astype(str) == c).sum() for c in categories])
        cur_counts = np.array([(current.astype(str) == c).sum() for c in categories])

    ref_pct = np.maximum(ref_counts / max(ref_counts.sum(), 1), _EPSILON)
    cur_pct = np.maximum(cur_counts / max(cur_counts.sum(), 1), _EPSILON)
    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def ks_statistic(reference: pd.Series, current: pd.Series) -> float:
    """Two-sample KS statistic for a numeric feature. 0.0 when either side is
    empty or the feature is non-numeric."""
    reference = reference.dropna()
    current = current.dropna()
    if reference.empty or current.empty:
        return 0.0
    if not (
        pd.api.types.is_numeric_dtype(reference) and pd.api.types.is_numeric_dtype(current)
    ):
        return 0.0
    from scipy.stats import ks_2samp

    return float(ks_2samp(reference, current).statistic)


def detect_drift(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    features: list[str] | None = None,
    method: str = "psi",
    threshold: float = PSI_SIGNIFICANT,
) -> DriftReport:
    """Per-feature drift between a reference window and a current one.

    Only columns present in *both* frames are compared; a column that exists in
    one and not the other is a schema change for `ingest/` to catch, not drift.
    """
    shared = [c for c in (features or list(reference.columns)) if c in current.columns]

    drifts: list[FeatureDrift] = []
    for column in shared:
        if method == "ks":
            statistic = ks_statistic(reference[column], current[column])
        else:
            statistic = population_stability_index(reference[column], current[column])
        drifts.append(
            FeatureDrift(
                feature=column,
                statistic=statistic,
                method="ks" if method == "ks" else "psi",
                drifted=statistic > threshold,
            )
        )

    return DriftReport(
        features=tuple(drifts),
        reference_rows=len(reference),
        current_rows=len(current),
    )


def train_serve_skew(
    training_row: dict[str, float],
    serving_row: dict[str, float],
    tolerance: float = 1e-6,
) -> dict[str, str]:
    """Compare one identical entity's features as computed by each path.

    Returns feature -> description of the disagreement; empty means the paths
    agree. Run on a handful of known rows, not in aggregate: aggregate statistics
    can match exactly while every individual row is computed wrongly.
    """
    skewed: dict[str, str] = {}
    for feature in sorted(set(training_row) | set(serving_row)):
        if feature not in training_row:
            skewed[feature] = "computed at serving time only"
            continue
        if feature not in serving_row:
            skewed[feature] = "computed at training time only"
            continue
        train_value, serve_value = training_row[feature], serving_row[feature]
        if train_value is None or serve_value is None:
            if train_value is not serve_value:
                skewed[feature] = f"null on one side: train={train_value}, serve={serve_value}"
            continue
        if abs(float(train_value) - float(serve_value)) > tolerance:
            skewed[feature] = f"train={train_value}, serve={serve_value}"
    return skewed
