"""Every registry entry must survive `random_state=seed` — the seed-alias gap.

This closes a real escape. `_catboost_clf` set `random_seed` while every workflow
passes `random_state`; CatBoost treats the two as aliases and rejects having both
initialized. The 168-test suite missed it because no test called a factory with
`random_state` for that model, so catboost failed on every call through a
workflow, was caught by the workflow's own except-and-log, and vanished from the
comparison table as a "skipped" model.

The non-obvious part, and the reason this file tests what it does: **construction
succeeds**. `CatBoostClassifier(random_seed=42, random_state=42)` builds without
complaint and only raises at `fit()`. A test that asserted `spec.build(
random_state=42)` did not raise would therefore have passed against the broken
code and caught nothing. So the seeded test fits.

Estimators that legitimately take no `random_state` (DBSCAN, AgglomerativeClustering,
LinearRegression) are expected to reject it — they are asserted to reject it
loudly, which is the honest outcome, rather than being skipped silently.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.selection.registry import REGISTRY, ReservedModelError, get_models

SEED = 42

NO_RANDOM_STATE = {"dbscan", "agglomerative", "linear"}
"""Specs whose underlying estimator has no random_state parameter at all."""

RESERVED = {"bandit"}
"""Registered-but-unimplemented specs — they raise by design."""


@pytest.fixture
def tiny_supervised():
    """A small, separable binary frame — enough for every classifier to fit."""
    rng = np.random.default_rng(SEED)
    n = 80
    x = pd.DataFrame(
        {
            "a": np.concatenate([rng.normal(0, 1, n // 2), rng.normal(3, 1, n // 2)]),
            "b": np.concatenate([rng.normal(0, 1, n // 2), rng.normal(-3, 1, n // 2)]),
        }
    )
    y = pd.Series([0] * (n // 2) + [1] * (n // 2))
    return x, y


@pytest.fixture
def tiny_unsupervised():
    rng = np.random.default_rng(SEED)
    return pd.DataFrame(
        {
            "a": np.concatenate([rng.normal(0, 1, 40), rng.normal(5, 1, 40)]),
            "b": np.concatenate([rng.normal(0, 1, 40), rng.normal(5, 1, 40)]),
        }
    )


def _available_specs():
    return [s for s in REGISTRY.specs if s.available]


@pytest.mark.parametrize("spec", _available_specs(), ids=lambda s: s.name)
def test_every_spec_builds_with_random_state(spec):
    """Construction with `random_state` must not raise for a seedable spec."""
    if spec.name in RESERVED:
        with pytest.raises(ReservedModelError):
            spec.build(random_state=SEED)
        return
    if spec.name in NO_RANDOM_STATE:
        with pytest.raises(TypeError, match="random_state"):
            spec.build(random_state=SEED)
        return
    assert spec.build(random_state=SEED) is not None


@pytest.mark.parametrize(
    "spec",
    [s for s in _available_specs() if s.name not in RESERVED | NO_RANDOM_STATE],
    ids=lambda s: s.name,
)
def test_every_seedable_spec_fits_with_random_state(spec, tiny_supervised, tiny_unsupervised):
    """The assertion that actually catches the catboost alias conflict.

    Construction is not enough — CatBoost accepts both seed spellings at
    `__init__` and rejects them at `fit`. Fitting is the only place the conflict
    surfaces, so fitting is what this asserts.
    """
    estimator = spec.build(random_state=SEED)
    if spec.family == "clustering":
        estimator.fit(tiny_unsupervised)
    else:
        x, y = tiny_supervised
        target = y if spec.family == "classification" else y.astype(float)
        estimator.fit(x, target)


def test_get_models_threads_random_state_through_every_candidate(tiny_supervised):
    """The workflow path: `get_models(..., random_state=seed)` then fit each.

    This is the exact call shape the classification workflow makes, and the one
    that silently dropped catboost.
    """
    x, y = tiny_supervised
    models = get_models("classification", "binary", random_state=SEED)

    assert models, "expected at least the logistic baseline"
    for name, estimator in models.items():
        estimator.fit(x, y)
        assert hasattr(estimator, "predict"), f"{name} did not fit into a usable estimator"


def test_catboost_collapses_the_seed_alias():
    """Regression test, named for the bug.

    CatBoost must end up with exactly one of random_seed/random_state set, and it
    must carry the caller's value — not the factory default.
    """
    pytest.importorskip("catboost")
    from ml.selection.registry import get_spec

    estimator = get_spec("catboost").build(random_state=7)
    params = estimator.get_params()
    seed_params = {k: v for k, v in params.items() if k in {"random_seed", "random_state"}}

    assert len(seed_params) == 1, f"both seed spellings are live: {seed_params}"
    assert next(iter(seed_params.values())) == 7, "the caller's seed was discarded"
