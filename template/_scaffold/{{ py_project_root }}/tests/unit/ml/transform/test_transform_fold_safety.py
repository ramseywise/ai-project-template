"""`transform/` fits inside a fold and nowhere else (naming.md §3 rule 3).

Before this file the claim was carried only by `RunResult.transform_fitted_in_fold`
and checked only by the classification workflow — so a transformer used directly,
outside that one workflow, had nothing asserting it. A rule enforced at exactly one
call site is a rule about that call site, not about the stage.

The test that matters here is the *differencing* one: fit a transformer on a
subset, fit an identical one on the full frame, and assert the learned statistics
differ. If they cannot differ, the transformer has no fitted state and leakage is
impossible; if they do differ, then fitting on the full frame demonstrably leaks
information about held-out rows, and the only safe place to fit is inside a
`Pipeline` the splitter drives.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline

from ml.evaluation.compare import TabularPreprocessor
from ml.transform.encoders import TargetEncoder

SEED = 42


@pytest.fixture
def skewed_frame():
    """A frame whose first and second halves have very different distributions.

    The split is deliberate: a statistic fitted on the whole frame is then
    provably different from one fitted on either half, which is what makes
    leakage observable rather than a matter of opinion.
    """
    rng = np.random.default_rng(SEED)
    first = pd.DataFrame({"x": rng.normal(0, 1, 60), "cat": ["a"] * 60})
    second = pd.DataFrame({"x": rng.normal(50, 1, 60), "cat": ["b"] * 60})
    frame = pd.concat([first, second], ignore_index=True)
    y = pd.Series([0] * 60 + [1] * 60)
    return frame, y


def test_preprocessor_statistics_depend_on_the_rows_it_saw(skewed_frame):
    """The leakage mechanism, made concrete.

    The imputer's median and the scaler's mean are fitted state. Fitting on the
    full frame gives different values than fitting on a fold — which is exactly
    the information that must not cross the split boundary.
    """
    frame, _ = skewed_frame

    on_fold = TabularPreprocessor(numeric_features=["x"], categorical_features=[])
    on_fold.fit(frame.iloc[:60])

    on_full = TabularPreprocessor(numeric_features=["x"], categorical_features=[])
    on_full.fit(frame)

    assert on_fold.scaler is not None and on_full.scaler is not None
    fold_mean = float(on_fold.scaler.mean_[0])
    full_mean = float(on_full.scaler.mean_[0])

    assert not np.isclose(fold_mean, full_mean), (
        "the scaler learned the same mean from a fold as from the full frame; "
        "if that were true this stage would have no fitted state to leak"
    )


def test_preprocessor_is_usable_inside_a_pipeline(skewed_frame):
    """The prescribed usage must actually work end-to-end under a splitter.

    A rule that forbids the convenient thing has to leave a working alternative,
    or it gets ignored. `cross_val_score` refits the whole pipeline per fold, so
    every fitted statistic here is learned inside the fold.
    """
    frame, y = skewed_frame
    pipeline = make_pipeline(
        TabularPreprocessor(numeric_features=["x"], categorical_features=["cat"]),
        LogisticRegression(max_iter=1000),
    )

    scores = cross_val_score(
        pipeline,
        frame,
        y,
        cv=StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED),
        scoring="roc_auc",
    )

    assert len(scores) == 3
    assert np.all(np.isfinite(scores)), "the pipeline failed to fit inside a fold"


def test_target_encoder_holds_fitted_state_and_must_go_in_a_pipeline(skewed_frame):
    """`TargetEncoder` is the sharpest case — it fits *on the target*.

    A target encoder fitted outside the fold writes held-out label information
    into a feature column, which is the single most damaging form of leakage in
    tabular ML.
    """
    frame, y = skewed_frame
    categorical = frame[["cat"]]

    fold_encoder = TargetEncoder().fit(categorical.iloc[:90], y.iloc[:90])
    full_encoder = TargetEncoder().fit(categorical, y)

    fold_out = fold_encoder.transform(categorical)
    full_out = full_encoder.transform(categorical)

    assert not np.allclose(fold_out, full_out), (
        "the target encoder produced identical output whether or not it saw the "
        "held-out rows' labels — it must have fitted state for the fold rule to bite"
    )
    assert fold_encoder.global_mean_ != full_encoder.global_mean_, (
        "the global mean is fitted from the target; seeing more rows must change it"
    )
