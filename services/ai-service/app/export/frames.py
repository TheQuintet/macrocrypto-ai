"""Shared per-data-type frame builders for the export package.

Both the CSV exporter (A2.2) and the PNG exporter (A2.3) render the
same four derived data streams over a chosen timeframe:

    - btc_price    — hourly BTC observation rows
    - macro        — hourly macro indicator rows
    - predictions  — latest stored batch per (horizon, model)
    - correlations — latest correlation per (indicator, window)
    - regimes      — hourly regime label, computed on the fly

Rather than maintain two copies of the fetch/merge/tag logic, both
exporters call the functions in this module. The CSV exporter wraps
the results in a pandas DataFrame; the PNG exporter plots them. Any
future export format (PDF in A2.4, metadata block in A2.5) plugs in
here as well.

Design:

    - Pure: each builder takes the repository it needs and returns
      a DataFrame. No session, no I/O, no filesystem.
    - The leading ``data_type`` column tags each row so a
      multi-type frame stays self-describing. This mirrors the CSV
      exporter's behaviour from A2.2.
    - Timestamps are converted to ISO 8601 strings for the same
      reason as A2.2: whatever the consumer (CSV writer, chart
      axis, PDF table), ISO strings round-trip cleanly and read
      unambiguously.

The ``CsvExporter`` from A2.2 is a thin wrapper over these
functions. Its public API — ``ExportRequest``, ``ExportResult``,
``CsvExporter.build``, ``CsvExporter.to_csv``,
``CsvExporter._filename``, and the module constants — is unchanged.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd

from app.database.repositories.correlation_repository import (
    CorrelationRepository,
)
from app.database.repositories.prediction_repository import (
    PredictionRepository,
)
from app.prediction.market import classify_market_condition_safe

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
# Timeframe label → hours. Every repository fetch in this module
# takes `hours`; the conversion happens exactly once, here.
TIMEFRAME_HOURS: Dict[str, int] = {
    "30d": 30 * 24,
    "90d": 90 * 24,
    "1y": 365 * 24,
    "5y": 5 * 365 * 24,
}

# Timeframe label → days. Used for the correlation lookback, which
# is expressed in days rather than hours.
TIMEFRAME_DAYS: Dict[str, int] = {
    "30d": 30,
    "90d": 90,
    "1y": 365,
    "5y": 5 * 365,
}

# The data types the *data* exporters produce. This is the CSV/PNG
# stream list, not the ``export_history.data_types`` value list —
# see app.database.validators for the storage-level enum, which
# also permits 'chart'.
SUPPORTED_DATA_TYPES = (
    "btc_price",
    "macro",
    "predictions",
    "correlations",
    "regimes",
)

# Rolling window size (in hours) used to compute a regime label for
# each row of the btc_price series. 30 days is the shortest window
# at which the A1.2 correlation calculator considers a series
# meaningful, so it is a defensible floor for a regime label too.
REGIME_ROLLING_WINDOW_HOURS = 30 * 24

# Predictions frame defaults. The A2.2 acceptance criteria say
# "prediction data export" without specifying a model or horizon,
# so we emit the latest batch for every (horizon, model_name) pair
# we know about, at the default 0.85 confidence.
PREDICTION_HORIZONS = ("24h", "7d")
PREDICTION_MODELS = (
    "prophet_fresh",
    "prophet_warm",
    "xgboost_fresh",
    "xgboost_incremental",
    "lightgbm_fresh",
    "lightgbm_incremental",
)
PREDICTION_CONFIDENCE = 0.85


# ============================================================
# SHARED HELPERS
# ============================================================
def tag(df: pd.DataFrame, data_type: str) -> pd.DataFrame:
    """Insert a leading ``data_type`` column.

    A no-op when ``df`` is empty in the sense that the column is
    still added (so the concatenated frame has a stable header),
    but no rows are created.

    Args:
        df: The frame to tag.
        data_type: The value to write into every row.

    Returns:
        The tagged frame (a new object; ``df`` is not mutated).
    """
    if df.empty:
        out = df.copy()
        out.insert(0, "data_type", pd.Series(dtype="object"))
        return out

    out = df.copy()
    out.insert(0, "data_type", data_type)
    return out


def stringify_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """Convert any datetime-typed column to ISO 8601 strings.

    ``pandas.to_csv`` renders datetimes in a format that is readable
    but not always parseable without hints on re-import. ISO 8601
    strings round-trip cleanly through ``pandas.read_csv`` and
    render cleanly on a matplotlib axis.

    Args:
        df: The frame to normalise.

    Returns:
        The frame with datetime columns converted to strings.
    """
    if df.empty:
        return df

    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = out[col].apply(
                lambda v: v.isoformat() if v is not None else None
            )
    return out


# ============================================================
# PER-DATA-TYPE BUILDERS
# ============================================================
async def build_btc_price_frame(
    prediction_repo: PredictionRepository,
    hours: int,
) -> pd.DataFrame:
    """Build the BTC price data frame.

    Wraps ``PredictionRepository.fetch_recent_btc_data``. The
    repository already returns columns: time, close, volume,
    volatility, dominance, active_addresses, price_lag_7d.

    Args:
        prediction_repo: The prediction repository.
        hours: Number of most recent hours to fetch.

    Returns:
        DataFrame tagged with ``data_type='btc_price'``.
    """
    df = await prediction_repo.fetch_recent_btc_data(hours=hours)
    df = tag(df, "btc_price")
    return stringify_timestamps(df)


async def build_macro_frame(
    prediction_repo: PredictionRepository,
    hours: int,
) -> pd.DataFrame:
    """Build the macroeconomic indicator data frame.

    Wraps ``PredictionRepository.fetch_recent_macro_data``. The
    repository returns columns: time, cpi, interest_rate,
    m2_growth, dxy, treasury_yield.

    Args:
        prediction_repo: The prediction repository.
        hours: Number of most recent hours to fetch.

    Returns:
        DataFrame tagged with ``data_type='macro'``.
    """
    df = await prediction_repo.fetch_recent_macro_data(hours=hours)
    df = tag(df, "macro")
    return stringify_timestamps(df)


async def build_predictions_frame(
    prediction_repo: PredictionRepository,
    hours: int,
) -> pd.DataFrame:
    """Build the prediction data frame.

    Emits the latest stored batch for every (horizon, model_name)
    pair at the default confidence. Pairs with no stored rows are
    omitted from the output; they do not raise. The caller's
    empty-frame check catches the "every pair is missing" case.

    The ``hours`` argument is accepted for signature parity with
    the other builders but is not used — the latest-batch lookup in
    ``PredictionRepository.fetch_latest_predictions`` is already
    scoped by horizon, and the horizon (24h or 7d) bounds the
    batch length.

    Args:
        prediction_repo: The prediction repository.
        hours: Unused. Accepted for a uniform dispatch signature.

    Returns:
        DataFrame tagged with ``data_type='predictions'``.
    """
    rows: List[Dict[str, Any]] = []

    for horizon in PREDICTION_HORIZONS:
        for model_name in PREDICTION_MODELS:
            batch = await prediction_repo.fetch_latest_predictions(
                horizon=horizon,
                model_name=model_name,
                confidence=PREDICTION_CONFIDENCE,
            )
            for p in batch:
                rows.append(
                    {
                        "model_name": p.model_name,
                        "horizon": p.horizon,
                        "confidence": p.confidence,
                        "prediction_time": p.prediction_time,
                        "forecast_time": p.time,
                        "predicted_price": p.predicted_price,
                        "lower_bound": p.lower_bound,
                        "upper_bound": p.upper_bound,
                    }
                )

    df = pd.DataFrame(rows)
    df = tag(df, "predictions")
    return stringify_timestamps(df)


async def build_correlations_frame(
    correlation_repo: CorrelationRepository,
    days: int,
) -> pd.DataFrame:
    """Build the correlation data frame.

    Emits the latest row per (indicator, window) across all
    windows. The ``days`` argument is accepted for signature parity
    with the other builders but is not used — the repository's
    "latest per indicator" query already returns one row per pair
    regardless of how recent the row is.

    Args:
        correlation_repo: The correlation repository.
        days: Unused. Accepted for a uniform dispatch signature.

    Returns:
        DataFrame tagged with ``data_type='correlations'``.
    """
    rows = await correlation_repo.fetch_latest_per_indicator()
    df = pd.DataFrame(rows)
    df = tag(df, "correlations")
    return stringify_timestamps(df)


async def build_regimes_frame(
    prediction_repo: PredictionRepository,
    hours: int,
) -> pd.DataFrame:
    """Build the regime data frame.

    Regime labels are computed on the fly per row from a rolling
    window of the BTC close series. Each row's label describes the
    market condition over the preceding
    ``REGIME_ROLLING_WINDOW_HOURS`` hours, as classified by
    ``classify_market_condition_safe``. There is no ``regimes``
    table; the labels live only in the export.

    Rows before the rolling window has filled are still emitted,
    with a ``None`` label — the A2.2 acceptance criteria call for
    regime data over the requested timeframe, not for a minimum
    history requirement.

    Args:
        prediction_repo: The prediction repository.
        hours: Number of most recent hours to fetch.

    Returns:
        DataFrame tagged with ``data_type='regimes'`` with
        columns: time, close, regime.
    """
    btc_df = await prediction_repo.fetch_recent_btc_data(hours=hours)

    if btc_df.empty:
        return tag(btc_df, "regimes")

    closes = btc_df["close"].tolist()
    labels: List[Optional[str]] = []
    for i in range(len(closes)):
        window_start = max(0, i + 1 - REGIME_ROLLING_WINDOW_HOURS)
        window = closes[window_start : i + 1]
        labels.append(classify_market_condition_safe(window))

    out = pd.DataFrame(
        {
            "time": btc_df["time"].tolist(),
            "close": closes,
            "regime": labels,
        }
    )
    out = tag(out, "regimes")
    return stringify_timestamps(out)


__all__ = [
    "PREDICTION_CONFIDENCE",
    "PREDICTION_HORIZONS",
    "PREDICTION_MODELS",
    "REGIME_ROLLING_WINDOW_HOURS",
    "SUPPORTED_DATA_TYPES",
    "TIMEFRAME_DAYS",
    "TIMEFRAME_HOURS",
    "build_btc_price_frame",
    "build_correlations_frame",
    "build_macro_frame",
    "build_predictions_frame",
    "build_regimes_frame",
    "stringify_timestamps",
    "tag",
]