"""Evaluation stage — split plans, metrics, and comparison against a baseline.

The split comes first deliberately. Metrics computed over a leaky split are
precise measurements of nothing, so `splitting.py` is the module the rest of
this package depends on being correct.

Calibration and threshold choice used to live here and now live in
`ml.calibration`. They were split out because they consume *costs* — a business
input, not a model output — and mixing the two is what makes a pipeline
un-reviewable (naming.md §3 rule 2). Import them from `ml.calibration`; they are
deliberately not re-exported here, so the stage boundary stays visible at the
call site.
"""

from __future__ import annotations

from ml.evaluation.baselines import (
    MetricVerdict,
    RunVerdict,
    check_absolute,
    check_baseline,
    load_targets,
    write_baseline,
)
from ml.evaluation.compare import (
    ModelComparisonResult,
    ModelCVResult,
    TabularPreprocessor,
    compare_classifiers,
    default_baseline_models,
)
from ml.evaluation.metrics import (
    ClassificationMetrics,
    ClusteringMetrics,
    CurvePoints,
    RegressionMetrics,
    classification_metrics,
    clustering_metrics,
    pr_curve,
    precision_at_k,
    regression_metrics,
    roc_curve_points,
)
from ml.evaluation.splitting import (
    DEFAULT_N_SPLITS,
    RANDOM_STATE,
    GroupLeakageError,
    SortedTimeSeriesSplit,
    SplitPlan,
    TemporalLeakageError,
    assert_no_group_leakage,
    assert_temporal_order,
    make_splitter,
)

__all__ = [
    "DEFAULT_N_SPLITS",
    "RANDOM_STATE",
    "ClassificationMetrics",
    "ClusteringMetrics",
    "CurvePoints",
    "GroupLeakageError",
    "MetricVerdict",
    "ModelCVResult",
    "ModelComparisonResult",
    "RegressionMetrics",
    "RunVerdict",
    "SortedTimeSeriesSplit",
    "SplitPlan",
    "TabularPreprocessor",
    "TemporalLeakageError",
    "assert_no_group_leakage",
    "assert_temporal_order",
    "check_absolute",
    "check_baseline",
    "classification_metrics",
    "clustering_metrics",
    "compare_classifiers",
    "default_baseline_models",
    "load_targets",
    "make_splitter",
    "pr_curve",
    "precision_at_k",
    "regression_metrics",
    "roc_curve_points",
    "write_baseline",
]
