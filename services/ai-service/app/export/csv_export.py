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
    - The per-data-type frame builders live in ``app.export.frames``
      and are shared with the PNG exporter (A2.3). This module stays
      a thin CSV renderer on top of those frames, so the fetch path
      for any given data type exists in exactly one place across the
      A2 ticket family.
    - Timeframe → hour conversion is a static map defined in
      ``app.export.frames`` and re-exported here. The acceptance
      criteria call for 30d / 90d / 1y / 5y; every downstream fetch
      takes ``hours``, so we convert once and never again.
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
from app.export.frames import (
    PREDICTION_CONFIDENCE,
    PREDICTION_HORIZONS,
    PREDICTION_MODELS,
    REGIME_ROLLING_WINDOW_HOURS,
    SUPPORTED_DATA_TYPES,
    TIMEFRAME_DAYS,
    TIMEFRAME_HOURS,
    build_btc_price_frame,
    build_correlations_frame,
    build_macro_frame,
    build_predictions_frame,
    build_regimes_frame,
)

logger = logging.getLogger(__name__)


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
            2. For each requested data type, build a DataFrame via
               ``app.export.frames``.
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
    # PER-DATA-TYPE DISPATCH
    # ============================================================
    async def _build_frame(
        self,
        data_type: str,
        hours: int,
        days: int,
    ) -> pd.DataFrame:
        """Dispatch to the per-type builder for the given data type.

        Delegates to ``app.export.frames``, which is shared with
        the PNG exporter (A2.3). Each builder returns a DataFrame
        with a leading ``data_type`` column whose value equals the
        requested type.

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
        """Delegate to ``frames.build_btc_price_frame``.

        Kept as a thin method for internal-shape compatibility; the
        shared logic lives in ``app.export.frames``.
        """
        return await build_btc_price_frame(self._prediction_repo, hours)

    async def _build_macro_frame(self, hours: int) -> pd.DataFrame:
        """Delegate to ``frames.build_macro_frame``.

        Kept as a thin method for internal-shape compatibility; the
        shared logic lives in ``app.export.frames``.
        """
        return await build_macro_frame(self._prediction_repo, hours)

    async def _build_predictions_frame(self, hours: int) -> pd.DataFrame:
        """Delegate to ``frames.build_predictions_frame``.

        Kept as a thin method for internal-shape compatibility; the
        shared logic lives in ``app.export.frames``.
        """
        return await build_predictions_frame(self._prediction_repo, hours)

    async def _build_correlations_frame(self, days: int) -> pd.DataFrame:
        """Delegate to ``frames.build_correlations_frame``.

        Kept as a thin method for internal-shape compatibility; the
        shared logic lives in ``app.export.frames``.
        """
        return await build_correlations_frame(
            self._correlation_repo, days
        )

    async def _build_regimes_frame(self, hours: int) -> pd.DataFrame:
        """Delegate to ``frames.build_regimes_frame``.

        Kept as a thin method for internal-shape compatibility; the
        shared logic lives in ``app.export.frames``.
        """
        return await build_regimes_frame(self._prediction_repo, hours)

    # ============================================================
    # HELPERS
    # ============================================================
    @staticmethod
    def _tag(df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """Backwards-compatible alias for ``frames.tag``.

        ``build()`` no longer calls this directly — the shared
        builders in ``app.export.frames`` tag their own frames. The
        alias is kept so that any existing caller (or test) that
        reaches for ``CsvExporter._tag`` continues to work.
        """
        from app.export.frames import tag as _frames_tag

        return _frames_tag(df, data_type)

    @staticmethod
    def _stringify_timestamps(df: pd.DataFrame) -> pd.DataFrame:
        """Backwards-compatible alias for ``frames.stringify_timestamps``.

        See ``_tag`` for why the alias exists.
        """
        from app.export.frames import (
            stringify_timestamps as _frames_stringify,
        )

        return _frames_stringify(df)

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