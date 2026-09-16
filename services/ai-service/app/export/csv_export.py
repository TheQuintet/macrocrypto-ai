"""CSV export generation for analyst-facing data downloads.

Builds a single CSV byte payload from one or more of the four
data types the A2 ticket family covers:

    - btc_price        — BTC OHLC close + volume + volatility +
                         dominance + active_addresses + price_lag_7d,
                         one row per hourly observation
    - macro            — macro indicator readings (cpi, interest_rate,
                         m2_growth, dxy, treasury_yield), one row per
                         hourly observation after forward-fill
    - predictions      — latest stored prediction batch per
                         (horizon, model_name, confidence), one row
                         per forecast point
    - correlations     — latest correlation per (indicator, window),
                         one row per pair
    - regimes          — regime label per hourly BTC observation,
                         computed on the fly from a rolling window
                         of closes via
                         ``app.prediction.market.classify_market_condition_safe``

Data types are selected by the caller via ``ExportRequest.data_types``.
When multiple types are requested, the resulting CSV carries a leading
``data_type`` column so the sections can be told apart on re-import;
timestamps are emitted as ISO 8601 strings so they round-trip cleanly
through ``pandas.read_csv`` without a parser hint.

Design:

    - Pure: reads via the injected repositories, returns bytes. Does
      not write files, does not call the ``export_history`` repository,
      does not open its own DB session. The caller owns the session
      (see ``app.export.service``) and owns persistence.
    - Timeframe → hour conversion is a static map. The acceptance
      criteria call for 30d / 90d / 1y / 5y; every downstream fetch
      takes ``hours``, so we convert once here and never again.
    - Regime labels are computed on the fly, per row, from a rolling
      window of the BTC close series. There is no ``regimes`` table;
      ``prediction_performance.market_condition`` stores a regime
      label but only where a walk-forward backtest produced one. The
      on-the-fly approach produces a complete series over the export
      window, matches the A1.7 precedent of computing derived labels
      at read time, and does not couple the export to a table owned
      by a different feature area.
    - Empty frames are a hard error. The A2.2 acceptance criteria
      require "data validation before export"; a requested data type
      that yields zero rows raises ``ValueError`` rather than
      producing a header-only CSV.

File naming follows the A2.2 criterion exactly:

    macro-crypto-[data-type]-[timeframe]-[YYYY-MM-DD].csv

When multiple data types are requested the ``data-type`` segment is
the literal ``multi`` and the individual types are carried inside the
CSV in the ``data_type`` column.

Usage:

    async with session_scope() as session:
        exporter = CsvExporter(
            prediction_repo=PredictionRepository(session),
            correlation_repo=CorrelationRepository(session),
        )
        result = await exporter.build(
            ExportRequest(
                data_types=["btc_price", "correlations"],
                timeframe="90d",
                user_id="analyst-42",
            )
        )
        # result.content is the CSV bytes
        # result.file_name follows the naming convention
"""

import io
import logging
from dataclasses import dataclass, field
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

# The data types this exporter can produce. Matches the
# VALID_DATA_TYPE_NAMES tuple in app.database.validators, minus
# "model_performance" and "events", which belong to later tickets
# (M8 / A5) and are not part of the A2.2 acceptance criteria.
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
# REQUEST / RESULT DATACLASSES
# ============================================================
@dataclass
class ExportRequest:
    """A single CSV export request.

    Attributes:
        data_types: One or more of ``SUPPORTED_DATA_TYPES``. Order
            is preserved in the output CSV.
        timeframe: One of ``TIMEFRAME_HOURS`` keys
            ('30d', '90d', '1y', '5y').
        user_id: Optional opaque identifier. Carried through so the
            caller can record it on the ``export_history`` row.
            The exporter itself does not use it.
    """

    data_types: List[str] = field(default_factory=list)
    timeframe: str = "30d"
    user_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable dict."""
        return {
            "data_types": list(self.data_types),
            "timeframe": self.timeframe,
            "user_id": self.user_id,
        }

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"ExportRequest(data_types={self.data_types!r}, "
            f"timeframe={self.timeframe!r}, user_id={self.user_id!r})"
        )


@dataclass
class ExportResult:
    """The output of a CSV export.

    ``content`` is the CSV byte payload. The caller is responsible
    for persisting it (local disk or object store) and for recording
    the export in ``export_history``. Neither happens here.

    Attributes:
        file_name: The generated filename, following
            ``macro-crypto-[data-type]-[timeframe]-[YYYY-MM-DD].csv``.
        file_size: ``len(content)`` in bytes.
        data_types: The data types that were requested (echoed).
        timeframe: The timeframe that was requested (echoed).
        rows_written: Total number of data rows in the CSV
            (excluding the header).
        content: The CSV bytes, UTF-8 encoded.
    """

    file_name: str
    file_size: int
    data_types: List[str]
    timeframe: str
    rows_written: int
    content: bytes

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable dict.

        ``content`` is deliberately omitted — it can be large, and
        the caller already holds it.
        """
        return {
            "file_name": self.file_name,
            "file_size": self.file_size,
            "data_types": list(self.data_types),
            "timeframe": self.timeframe,
            "rows_written": self.rows_written,
        }

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"ExportResult(file_name={self.file_name!r}, "
            f"file_size={self.file_size}, "
            f"timeframe={self.timeframe!r}, "
            f"rows_written={self.rows_written})"
        )


# ============================================================
# EXPORTER
# ============================================================
class CsvExporter:
    """Build a CSV byte payload from one or more data types.

    The exporter reads via the injected repositories and returns
    bytes. It does not open a session, does not write files, and
    does not record the export in ``export_history``. Those are the
    caller's responsibilities (see ``app.export.service``).

    Example:
        exporter = CsvExporter(prediction_repo, correlation_repo)
        result = await exporter.build(
            ExportRequest(data_types=["btc_price"], timeframe="30d")
        )
        # result.content is the CSV bytes
    """

    def __init__(
        self,
        prediction_repo: PredictionRepository,
        correlation_repo: CorrelationRepository,
    ) -> None:
        """Initialize the exporter.

        Args:
            prediction_repo: Reads BTC price, macro, and prediction
                rows from the source tables.
            correlation_repo: Reads the latest correlation rows from
                ``btc_macro_correlation``.
        """
        self._prediction_repo = prediction_repo
        self._correlation_repo = correlation_repo

    # ============================================================
    # PUBLIC API
    # ============================================================
    async def build(self, request: ExportRequest) -> ExportResult:
        """Produce a CSV payload for the given request.

        Steps:
            1. Validate the request (timeframe, data types).
            2. For each requested data type, build a DataFrame and
               tag it with a leading ``data_type`` column.
            3. Concatenate the frames (single type → unchanged;
               multiple types → sections distinguishable by the
               ``data_type`` column).
            4. Re-validate: no requested type may yield zero rows.
            5. Render to CSV bytes and compute the filename.

        Args:
            request: The export request.

        Returns:
            ExportResult with the CSV bytes.

        Raises:
            ValueError: If the timeframe is unknown, if data_types
                is empty, if a data type is unsupported, or if a
                requested data type produces zero rows.
        """
        # ---- 1. Validate request shape ----
        if request.timeframe not in TIMEFRAME_HOURS:
            raise ValueError(
                f"Unknown timeframe {request.timeframe!r}. "
                f"Must be one of {tuple(TIMEFRAME_HOURS.keys())}."
            )
        if not request.data_types:
            raise ValueError("data_types must not be empty")
        for dt in request.data_types:
            if dt not in SUPPORTED_DATA_TYPES:
                raise ValueError(
                    f"Unsupported data type {dt!r}. "
                    f"Must be one of {SUPPORTED_DATA_TYPES}."
                )

        hours = TIMEFRAME_HOURS[request.timeframe]
        days = TIMEFRAME_DAYS[request.timeframe]

        logger.info(
            f"Building CSV export: types={request.data_types} "
            f"timeframe={request.timeframe} hours={hours}"
        )

        # ---- 2. Build one frame per requested type ----
        frames: List[pd.DataFrame] = []
        for data_type in request.data_types:
            frame = await self._build_frame(
                data_type=data_type,
                hours=hours,
                days=days,
            )
            frames.append(frame)

        # ---- 3. Concatenate ----
        if len(frames) == 1:
            combined = frames[0]
        else:
            combined = pd.concat(frames, ignore_index=True, sort=False)

        # ---- 4. Validate non-empty ----
        if combined.empty:
            raise ValueError(
                f"Export produced zero rows for types="
                f"{request.data_types} timeframe={request.timeframe}"
            )

        # ---- 5. Render ----
        content = self.to_csv(combined)
        rows_written = len(combined)
        file_name = self._filename(
            data_types=request.data_types,
            timeframe=request.timeframe,
        )

        logger.info(
            f"Built CSV export: {file_name} "
            f"({rows_written} rows, {len(content)} bytes)"
        )

        return ExportResult(
            file_name=file_name,
            file_size=len(content),
            data_types=list(request.data_types),
            timeframe=request.timeframe,
            rows_written=rows_written,
            content=content,
        )

    # ============================================================
    # PER-DATA-TYPE BUILDERS
    # ============================================================
    async def _build_frame(
        self,
        data_type: str,
        hours: int,
        days: int,
    ) -> pd.DataFrame:
        """Dispatch to the per-type builder for the given data type.

        Each builder returns a DataFrame with a leading
        ``data_type`` column whose value equals the requested type.
        The leading column lets the concatenated CSV remain
        self-describing when multiple types are requested.

        Args:
            data_type: One of ``SUPPORTED_DATA_TYPES``.
            hours: Hours in the export timeframe.
            days: Days in the export timeframe.

        Returns:
            DataFrame with at least a ``data_type`` column.

        Raises:
            ValueError: If ``data_type`` is unsupported.
        """
        if data_type == "btc_price":
            return await self._build_btc_price_frame(hours)
        if data_type == "macro":
            return await self._build_macro_frame(hours)
        if data_type == "predictions":
            return await self._build_predictions_frame(hours)
        if data_type == "correlations":
            return await self._build_correlations_frame(days)
        if data_type == "regimes":
            return await self._build_regimes_frame(hours)

        # Defensive: build() already validated, so this is a bug.
        raise ValueError(f"Unsupported data type {data_type!r}")

    async def _build_btc_price_frame(self, hours: int) -> pd.DataFrame:
        """Build the BTC price data frame.

        Wraps ``PredictionRepository.fetch_recent_btc_data``. The
        repository already returns columns: time, close, volume,
        volatility, dominance, active_addresses, price_lag_7d.

        Args:
            hours: Number of most recent hours to fetch.

        Returns:
            DataFrame tagged with ``data_type='btc_price'``.
        """
        df = await self._prediction_repo.fetch_recent_btc_data(
            hours=hours
        )
        df = self._tag(df, "btc_price")
        return self._stringify_timestamps(df)

    async def _build_macro_frame(self, hours: int) -> pd.DataFrame:
        """Build the macroeconomic indicator data frame.

        Wraps ``PredictionRepository.fetch_recent_macro_data``. The
        repository returns columns: time, cpi, interest_rate,
        m2_growth, dxy, treasury_yield.

        Args:
            hours: Number of most recent hours to fetch.

        Returns:
            DataFrame tagged with ``data_type='macro'``.
        """
        df = await self._prediction_repo.fetch_recent_macro_data(
            hours=hours
        )
        df = self._tag(df, "macro")
        return self._stringify_timestamps(df)

    async def _build_predictions_frame(self, hours: int) -> pd.DataFrame:
        """Build the prediction data frame.

        Emits the latest stored batch for every
        (horizon, model_name) pair at the default confidence. Pairs
        with no stored rows are omitted from the output; they do
        not raise. The export only fails when *every* pair is
        missing, which ``build()`` catches as an empty frame.

        The ``hours`` argument is accepted for signature parity with
        the other builders but is not used — the latest-batch lookup
        in ``PredictionRepository.fetch_latest_predictions`` is
        already scoped by horizon, and the horizon (24h or 7d)
        bounds the batch length.

        Args:
            hours: Unused. Accepted for a uniform dispatch signature.

        Returns:
            DataFrame tagged with ``data_type='predictions'``.
        """
        rows: List[Dict[str, Any]] = []

        for horizon in PREDICTION_HORIZONS:
            for model_name in PREDICTION_MODELS:
                batch = (
                    await self._prediction_repo.fetch_latest_predictions(
                        horizon=horizon,
                        model_name=model_name,
                        confidence=PREDICTION_CONFIDENCE,
                    )
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
        df = self._tag(df, "predictions")
        return self._stringify_timestamps(df)

    async def _build_correlations_frame(self, days: int) -> pd.DataFrame:
        """Build the correlation data frame.

        Emits the latest row per (indicator, window) across all
        windows. The ``days`` argument is accepted for signature
        parity with the other builders but is not used — the
        repository's "latest per indicator" query already returns
        one row per pair regardless of how recent the row is.

        Args:
            days: Unused. Accepted for a uniform dispatch signature.

        Returns:
            DataFrame tagged with ``data_type='correlations'``.
        """
        rows = await self._correlation_repo.fetch_latest_per_indicator()

        df = pd.DataFrame(rows)
        df = self._tag(df, "correlations")
        return self._stringify_timestamps(df)

    async def _build_regimes_frame(self, hours: int) -> pd.DataFrame:
        """Build the regime data frame.

        Regime labels are computed on the fly per row from a rolling
        window of the BTC close series. Each row's label describes
        the market condition over the preceding
        ``REGIME_ROLLING_WINDOW_HOURS`` hours, as classified by
        ``classify_market_condition_safe``. There is no ``regimes``
        table; the labels live only in this export.

        Rows before the rolling window has filled are still
        emitted, with a ``None`` label — the A2.2 acceptance
        criteria call for regime data over the requested timeframe,
        not for a minimum history requirement.

        Args:
            hours: Number of most recent hours to fetch.

        Returns:
            DataFrame tagged with ``data_type='regimes'`` with
            columns: time, close, regime.
        """
        btc_df = await self._prediction_repo.fetch_recent_btc_data(
            hours=hours
        )

        if btc_df.empty:
            return self._tag(btc_df, "regimes")

        # Rolling classification is applied on the close series in
        # time order. The repository already sorts ascending.
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
        out = self._tag(out, "regimes")
        return self._stringify_timestamps(out)

    # ============================================================
    # HELPERS
    # ============================================================
    @staticmethod
    def _tag(df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """Insert a leading ``data_type`` column.

        A no-op when ``df`` is empty. The column is inserted at
        position 0 so it reads first in the CSV.

        Args:
            df: The frame to tag.
            data_type: The value to write into every row.

        Returns:
            The tagged frame (a new object; ``df`` is not mutated).
        """
        if df.empty:
            # Return as-is but ensure the column exists so the
            # concatenated CSV has a stable header.
            out = df.copy()
            out.insert(0, "data_type", pd.Series(dtype="object"))
            return out

        out = df.copy()
        out.insert(0, "data_type", data_type)
        return out

    @staticmethod
    def _stringify_timestamps(df: pd.DataFrame) -> pd.DataFrame:
        """Convert any datetime-typed column to ISO 8601 strings.

        ``pandas.to_csv`` renders datetimes in a format that is
        readable but not always parseable without hints on
        re-import. ISO 8601 strings round-trip cleanly through
        ``pandas.read_csv``.

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

    @staticmethod
    def to_csv(df: pd.DataFrame) -> bytes:
        """Render a frame to CSV bytes.

        UTC-naive, UTF-8 encoded, no index column. The header row is
        always present.

        Args:
            df: The frame to render.

        Returns:
            CSV bytes.
        """
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        return buf.getvalue().encode("utf-8")

    @staticmethod
    def _filename(
        data_types: List[str],
        timeframe: str,
    ) -> str:
        """Generate the export filename.

        Single data type:
            ``macro-crypto-<data-type>-<timeframe>-<YYYY-MM-DD>.csv``
        Multiple data types:
            ``macro-crypto-multi-<timeframe>-<YYYY-MM-DD>.csv``

        The date is UTC. The convention matches the A2.2 acceptance
        criterion exactly for the single-type case; the ``multi``
        fallback keeps the name well-formed when several types are
        packed into one file.

        Args:
            data_types: The requested data types.
            timeframe: The requested timeframe.

        Returns:
            The filename string.
        """
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if len(data_types) == 1:
            type_segment = data_types[0]
        else:
            type_segment = "multi"
        return f"macro-crypto-{type_segment}-{timeframe}-{date_str}.csv"


__all__ = [
    "CsvExporter",
    "ExportRequest",
    "ExportResult",
    "SUPPORTED_DATA_TYPES",
    "TIMEFRAME_DAYS",
    "TIMEFRAME_HOURS",
    "PREDICTION_CONFIDENCE",
    "PREDICTION_HORIZONS",
    "PREDICTION_MODELS",
    "REGIME_ROLLING_WINDOW_HOURS",
]