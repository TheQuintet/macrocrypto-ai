from collections.abc import Sequence

import pandas as pd

CONSTANT_FEATURE_COLUMNS_ATTR = "constant_feature_columns"
PROTECTED_COLUMNS = {
    "date",
    "ds",
    "observation_date",
    "label",
    "target",
    "target_next_price",
    "y",
}


def constant_feature_columns(data: pd.DataFrame) -> list[str]:
    """Return feature columns with at most one observed value."""
    if len(data) < 2:
        return []

    return [
        column
        for column in data.columns
        if column not in PROTECTED_COLUMNS
        and data[column].nunique(dropna=True) <= 1
    ]


def missing_required_columns(
    data: pd.DataFrame,
    required_columns: Sequence[str],
) -> list[str]:
    """Allow only columns explicitly removed as train-constant features."""
    removed_constants = set(
        data.attrs.get(CONSTANT_FEATURE_COLUMNS_ATTR, ())
    )
    return [
        column
        for column in required_columns
        if column not in data.columns and column not in removed_constants
    ]


def drop_rows_with_unhandled_missing_features(
    data: pd.DataFrame,
    feature_columns: Sequence[str],
    *,
    missing_feature: str,
    missing_indicator: str,
) -> pd.DataFrame:
    """Keep flagged missing feature values for estimators with native NaN support."""
    missing = data[feature_columns].isna()
    if missing_feature in feature_columns and missing_indicator in data.columns:
        flagged_missing = (
            data[missing_feature].isna() & data[missing_indicator].eq(1)
        )
        missing.loc[flagged_missing, missing_feature] = False

    return data.loc[~missing.any(axis=1)].reset_index(drop=True)
