"""Calibration stage — probability calibration, threshold policy, coverage bands.

Split out of `evaluation/` because the inputs differ in kind: evaluation measures
a model, calibration decides an *operating point*, and an operating point
consumes costs (`cost_fp`/`cost_fn`) which are a business input rather than
anything the model produces. Keeping them in one package is what let a threshold
be chosen inside a training run, where no one reviewing the model could see it.

`training/` must never import this package — see naming.md §3 rule 2.
"""

from __future__ import annotations

from ml.calibration.calibration import (
    CalibrationReport,
    assess_calibration,
    calibrate_classifier,
    expected_calibration_error,
    recommend_method,
    reliability_curve,
)
from ml.calibration.threshold import (
    ThresholdResult,
    choose_threshold,
    expected_cost,
    threshold_for_capacity,
)

__all__ = [
    "CalibrationReport",
    "ThresholdResult",
    "assess_calibration",
    "calibrate_classifier",
    "choose_threshold",
    "expected_calibration_error",
    "expected_cost",
    "recommend_method",
    "reliability_curve",
    "threshold_for_capacity",
]
