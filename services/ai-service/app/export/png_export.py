"""PNG chart export generation for analyst-facing downloads (A2.3).

Renders a single chart — BTC price over the chosen timeframe, with
a legend, axis labels, and a citations footer — into a 300 DPI PNG
byte payload.

The chart is deliberately minimal for A2.3:

    - One price line (BTC close) over the export window.
    - A title that names the timeframe.
    - Axis labels ("Time" / "Price (USD)").
    - A citations footer naming the data sources, the methodology,
      and the access time (A2.5).

Design:

    - Pure: reads via the injected ``PredictionRepository``,
      returns bytes. Does not write files, does not call the
      ``export_history`` repository, does not open its own DB
      session. The caller owns the session (see
      ``app.export.service``) and owns persistence.
    - The BTC price frame comes from
      ``app.export.frames.build_btc_price_frame`` — the same
      builder the CSV exporter uses. One fetch path for the A2
      ticket family.
    - The Figure construction and the PNG save step live in
      ``app.export.chart``, shared with the PDF exporter (A2.4).
      This module stays a thin format-specific wrapper.
    - The citations block is built here via
      ``app.export.metadata.build_metadata`` and carried on the
      returned ``ChartResult.metadata`` (A2.5).
    - matplotlib is used with the ``Agg`` backend (selected in
      ``app.export.chart``), which is headless-safe — no display
      required, correct for a server process and for CI.
    - Output resolution is fixed at 300 DPI, matching the A2.3
      acceptance criterion. The PNG's ``pHYs`` chunk carries the
      resolution; ``savefig(dpi=300)`` writes it.

File naming follows the A2.3 criterion exactly:

    macro-crypto-chart-[timeframe]-[YYYY-MM-DD].png

Usage:

    async with session_scope() as session:
        exporter = PngExporter(
            prediction_repo=PredictionRepository(session),
        )
        result = await exporter.render(
            ChartRequest(timeframe="90d", user_id="analyst-42")
        )
        # result.content is the PNG bytes
        # result.metadata is the citations block
        # result.file_name follows the naming convention
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import pandas as pd

from app.database.repositories.prediction_repository import (
    PredictionRepository,
)
from app.export.chart import (
    CHART_DATA_SOURCE,
    CHART_DPI,
    CHART_FIGSIZE_INCHES,
    build_chart_figure,
    save_figure_png,
)
from app.export.frames import (
    TIMEFRAME_HOURS,
    build_btc_price_frame,
)
from app.export.metadata import (
    ExportMetadata,
    build_metadata,
)

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
# The three chart constants now live in ``app.export.chart`` and
# are re-exported here so existing importers (including A2.3's own
# test module) keep working unchanged. The values are identical.


# ============================================================
# REQUEST / RESULT DATACLASSES
# ============================================================
@dataclass
class ChartRequest:
    """A single PNG chart request.

    Attributes:
        timeframe: One of ``TIMEFRAME_HOURS`` keys
            ('30d', '90d', '1y', '5y'). Also carried as the
            ``export_history.timeframe`` value.
        user_id: Optional opaque identifier. Carried through so
            the caller can record it on the ``export_history``
            row. The exporter itself does not use it.
        title: Optional override for the chart title. When None,
            a default title is derived from the timeframe.
    """

    timeframe: str = "30d"
    user_id: Optional[str] = None
    title: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable dict."""
        return {
            "timeframe": self.timeframe,
            "user_id": self.user_id,
            "title": self.title,
        }

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"ChartRequest(timeframe={self.timeframe!r}, "
            f"user_id={self.user_id!r})"
        )


@dataclass
class ChartResult:
    """The output of a PNG chart export.

    ``content`` is the PNG byte payload. The caller is responsible
    for persisting it (local disk or object store) and for
    recording the export in ``export_history``. Neither happens
    here.

    Attributes:
        file_name: The generated filename, following
            ``macro-crypto-chart-[timeframe]-[YYYY-MM-DD].png``.
        file_size: ``len(content)`` in bytes.
        timeframe: The timeframe that was requested (echoed).
        rows_plotted: Number of BTC price rows that were plotted.
        content: The PNG bytes.
        metadata: The citations block that was rendered into the
            chart footer (A2.5).
    """

    file_name: str
    file_size: int
    timeframe: str
    rows_plotted: int
    content: bytes
    metadata: Optional[ExportMetadata] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable dict.

        ``content`` is deliberately omitted — it can be large, and
        the caller already holds it.
        """
        d: Dict[str, Any] = {
            "file_name": self.file_name,
            "file_size": self.file_size,
            "timeframe": self.timeframe,
            "rows_plotted": self.rows_plotted,
        }
        if self.metadata is not None:
            d["metadata"] = self.metadata.to_dict()
        return d

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"ChartResult(file_name={self.file_name!r}, "
            f"file_size={self.file_size}, "
            f"timeframe={self.timeframe!r}, "
            f"rows_plotted={self.rows_plotted})"
        )


# ============================================================
# EXPORTER
# ============================================================
class PngExporter:
    """Render a single PNG chart from the BTC price series.

    The exporter reads via the injected repository and returns
    bytes. It does not open a session, does not write files, and
    does not record the export in ``export_history``. Those are
    the caller's responsibilities (see ``app.export.service``).

    Example:
        exporter = PngExporter(prediction_repo)
        result = await exporter.render(
            ChartRequest(timeframe="90d", user_id="analyst-42")
        )
        # result.content is the PNG bytes
    """

    def __init__(
        self,
        prediction_repo: PredictionRepository,
    ) -> None:
        """Initialize the exporter.

        Args:
            prediction_repo: Reads BTC price rows from the source
                tables. The same repository the CSV exporter uses.
        """
        self._prediction_repo = prediction_repo

    # ============================================================
    # PUBLIC API
    # ============================================================
    async def render(self, request: ChartRequest) -> ChartResult:
        """Render a PNG chart for the given request.

        Steps:
            1. Validate the timeframe.
            2. Build the BTC price frame via the shared
               ``frames.build_btc_price_frame``.
            3. Build the citations block via
               ``metadata.build_metadata``.
            4. Build the Figure via ``chart.build_chart_figure``.
            5. Save to a 300 DPI PNG byte buffer via
               ``chart.save_figure_png``.

        Args:
            request: The chart request.

        Returns:
            ChartResult with the PNG bytes and citations metadata.

        Raises:
            ValueError: If the timeframe is unknown, or if the
                BTC price frame is empty (nothing to plot).
        """
        # ---- 1. Validate request shape ----
        if request.timeframe not in TIMEFRAME_HOURS:
            raise ValueError(
                f"Unknown timeframe {request.timeframe!r}. "
                f"Must be one of {tuple(TIMEFRAME_HOURS.keys())}."
            )

        hours = TIMEFRAME_HOURS[request.timeframe]

        logger.info(
            f"Building PNG chart: timeframe={request.timeframe} "
            f"hours={hours}"
        )

        # ---- 2. Build the frame ----
        frame = await build_btc_price_frame(
            self._prediction_repo, hours
        )

        if frame.empty:
            raise ValueError(
                f"Chart produced zero rows for "
                f"timeframe={request.timeframe}"
            )

        # ---- 3. Citations block (A2.5) ----
        export_metadata = build_metadata(data_types=["chart"])

        # ---- 4. Build the Figure, then save ----
        content = self._render_png(
            frame=frame,
            timeframe=request.timeframe,
            title=request.title,
            metadata=export_metadata,
        )

        file_name = self._filename(timeframe=request.timeframe)
        rows_plotted = len(frame)

        logger.info(
            f"Built PNG chart: {file_name} "
            f"({rows_plotted} rows, {len(content)} bytes)"
        )

        return ChartResult(
            file_name=file_name,
            file_size=len(content),
            timeframe=request.timeframe,
            rows_plotted=rows_plotted,
            content=content,
            metadata=export_metadata,
        )

    # ============================================================
    # RENDERING
    # ============================================================
    @staticmethod
    def _render_png(
        frame: pd.DataFrame,
        timeframe: str,
        title: Optional[str],
        metadata: Optional[ExportMetadata] = None,
    ) -> bytes:
        """Render the frame to PNG bytes.

        Thin wrapper over ``chart.build_chart_figure`` +
        ``chart.save_figure_png``. The figure is closed inside
        ``save_figure_png``'s ``finally`` block, so no leak is
        possible even if ``savefig`` raises.

        Args:
            frame: A frame from ``frames.build_btc_price_frame``.
                Must have ``time`` and ``close`` columns.
            timeframe: The timeframe label, used in the default
                title and the footer.
            title: Optional title override.
            metadata: Citations block to render into the footer.
                When None, ``build_chart_figure`` builds a default
                block internally.

        Returns:
            PNG bytes.
        """
        fig = build_chart_figure(
            frame=frame,
            timeframe=timeframe,
            title=title,
            metadata=metadata,
        )
        return save_figure_png(fig)

    @staticmethod
    def _filename(timeframe: str) -> str:
        """Generate the chart filename.

        Follows the A2.3 criterion exactly:

            ``macro-crypto-chart-<timeframe>-<YYYY-MM-DD>.png``

        The date is UTC.

        Args:
            timeframe: The requested timeframe.

        Returns:
            The filename string.
        """
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"macro-crypto-chart-{timeframe}-{date_str}.png"


__all__ = [
    "CHART_DATA_SOURCE",
    "CHART_DPI",
    "CHART_FIGSIZE_INCHES",
    "ChartRequest",
    "ChartResult",
    "PngExporter",
]