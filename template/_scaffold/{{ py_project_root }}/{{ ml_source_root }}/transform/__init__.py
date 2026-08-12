"""Transform stage — column-type inference and the `ColumnTransformer` builder.

Everything here is fitted **inside a fold** by `training/`; nothing in this
package may be fitted on the full frame (naming.md §3 rule 3).

`TabularPreprocessor` is re-exported from `ml.evaluation.compare`, where it sits
next to the comparison harness that is its main caller. As of 2026-08-12 it is
imputer + scaler + one-hot (it was a `-9999` sentinel fill before), so it now
learns statistics at fit time and must go inside a `Pipeline` rather than being
applied to a frame before splitting. `numeric_strategy="sentinel"` restores the
old behaviour for a tree-only comparison.
"""

from __future__ import annotations

from ml.evaluation.compare import TabularPreprocessor
from ml.transform.columns import (
    DEFAULT_HIGH_CARD_THRESHOLD,
    ColumnPlan,
    infer_column_types,
)
from ml.transform.encoders import (
    DatetimeFeatures,
    TargetEncoder,
    build_transformer,
)

__all__ = [
    "DEFAULT_HIGH_CARD_THRESHOLD",
    "ColumnPlan",
    "DatetimeFeatures",
    "TabularPreprocessor",
    "TargetEncoder",
    "build_transformer",
    "infer_column_types",
]
