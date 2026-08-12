"""`features/` and the fold rule (naming.md §3 rule 3).

`features/` is a harder case than `transform/` and this file documents why rather
than pretending otherwise.

The functions here are **frame-level, not fitted transformers**: they take a
frame and return a wider frame. That shape has no `fit`, so it cannot be dropped
into a `Pipeline` and cannot be refitted per fold by a splitter. Whether calling
one leaks depends entirely on what it computes:

- **Row-local** (`add_ratio_features`, `add_interaction_features`,
  `add_calendar_features`): each output cell depends only on its own row. Safe to
  call before splitting — there is no cross-row statistic to leak.
- **Frame-dependent** (`collapse_rare_categories`, `add_group_aggregates`): the
  output depends on *other rows*. Calling these on the full frame before
  splitting leaks — and because they hold no fitted state, nothing in the type
  system or the object makes that leak visible. The caller has to know.

These tests pin both halves, so the distinction is enforced rather than being a
comment someone can drift away from.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.features.mining import (
    add_group_aggregates,
    add_interaction_features,
    add_ratio_features,
    collapse_rare_categories,
)

SEED = 42


@pytest.fixture
def two_halves():
    """A frame whose halves differ in category frequency and group means."""
    rng = np.random.default_rng(SEED)
    return pd.DataFrame(
        {
            "group": ["g1"] * 50 + ["g2"] * 50,
            "cat": (["common"] * 45 + ["rare"] * 5) + (["common"] * 25 + ["rare"] * 25),
            "value": np.concatenate([rng.normal(1, 0.1, 50), rng.normal(9, 0.1, 50)]),
            "other": rng.normal(5, 1, 100),
        }
    )


# ── row-local: safe before the split ─────────────────────────────────────────


def test_ratio_features_are_row_local(two_halves):
    """A ratio computed on a subset equals the same rows computed on the full
    frame — so calling it before splitting cannot leak."""
    frame = two_halves
    pairs = [("value", "other")]

    on_subset = add_ratio_features(frame.iloc[:50], pairs)["value_over_other"]
    on_full = add_ratio_features(frame, pairs)["value_over_other"].iloc[:50]

    pd.testing.assert_series_equal(on_subset, on_full)


def test_interaction_features_are_row_local(two_halves):
    frame = two_halves
    pairs = [("value", "other")]

    on_subset = add_interaction_features(frame.iloc[:50], pairs)
    on_full = add_interaction_features(frame, pairs).iloc[:50]

    new_columns = [c for c in on_subset.columns if c not in frame.columns]
    assert new_columns, "expected an interaction column to be added"
    for column in new_columns:
        pd.testing.assert_series_equal(on_subset[column], on_full[column])


# ── frame-dependent: leaks if called before the split ────────────────────────


def test_collapse_rare_categories_depends_on_the_whole_frame(two_halves):
    """The leak this file exists to name.

    `min_freq` is applied to frequencies computed from whatever frame is passed.
    The first half has 10% "rare"; the full frame has 30%. At a 20% threshold the
    same row collapses or not depending on rows the model should not have seen —
    and there is no fitted attribute anywhere to reveal that it happened.
    """
    frame = two_halves

    on_subset = collapse_rare_categories(frame.iloc[:50], ["cat"], min_freq=0.2)["cat"]
    on_full = collapse_rare_categories(frame, ["cat"], min_freq=0.2)["cat"].iloc[:50]

    assert not on_subset.equals(on_full), (
        "collapse_rare_categories gave the same answer on a fold as on the full "
        "frame; if that held it would not be frame-dependent and this warning "
        "could be dropped"
    )
    assert (on_subset == "__other__").any(), "expected 'rare' to collapse within the fold"
    assert not (on_full == "__other__").any(), (
        "expected 'rare' to survive when full-frame frequencies are used"
    )


def test_group_aggregates_depend_on_the_whole_frame():
    """Group means are cross-row statistics: computing them on the full frame
    writes held-out rows' values into every member of the group.

    The group must *straddle* the split for this to bite, which is the practical
    lesson. If a group lies wholly inside one side, its aggregate is unchanged and
    nothing leaks — grouped splitting (`GroupKFold`) is precisely the arrangement
    that guarantees that. The dangerous case is the ordinary one: a random split
    that cuts through groups, so a row's own group mean is partly computed from
    rows on the other side of the split.
    """
    straddling = pd.DataFrame(
        {
            "group": ["g1", "g2"] * 50,
            "value": [1.0, 1.0] * 25 + [9.0, 9.0] * 25,
        }
    )

    on_subset = add_group_aggregates(
        straddling.iloc[:50], group_col="group", value_cols=["value"]
    )
    on_full = add_group_aggregates(straddling, group_col="group", value_cols=["value"])
    frame = straddling

    aggregate_columns = [c for c in on_subset.columns if c not in frame.columns]
    assert aggregate_columns, "expected an aggregate column to be added"

    differs = any(
        not np.allclose(
            on_subset[column].to_numpy(dtype=float),
            on_full[column].iloc[:50].to_numpy(dtype=float),
            equal_nan=True,
        )
        for column in aggregate_columns
    )
    assert differs, (
        "group aggregates were identical whether or not held-out rows were "
        "visible — they must be frame-dependent for the fold rule to apply"
    )
