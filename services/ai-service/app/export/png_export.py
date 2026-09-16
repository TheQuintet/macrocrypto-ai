"""PNG chart export generation for analyst-facing downloads (A2.3).

Renders a single chart — BTC price over the chosen timeframe, with
a legend, axis labels, and a metadata footer — into a 300 DPI PNG
byte payload.

The chart is deliberately minimal for A2.3:

    - One price line (BTC close) over the export window.
    - A title that names the timeframe.
    - Axis labels ("Time" / "Price (USD)").
    - A footer line that names the data source and the render time.
      A2.5 will extend this into a proper citations block.

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
    - matplotlib is used with the ``Agg`` backend, which is
      headless-safe (no display required, correct for a server
      process and for CI). Every figure is closed in a ``finally``
      block so long-running processes do not leak figures.
    - Output resolution is fixed at 300 DPI, matching the A2.3
      acceptance criterion. The PNG's ``pHYs`` chunk carries the
      resolution; ``matplotlib.savefig(dpi=300)`` writes it.

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
        # result.file_name follows the naming convention
"""

import io
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import matplotlib

# Agg is the headless backend. It must be selected before pyplot
# is imported anywhere, and it must not be re-selected at import
# time of a module that another module might already have used to
# pull in pyplot. Importing pyplot *after* use("Agg") is the
# documented-safe order.
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402  (after matplotlib.use)
import pandas as pd  # noqa: E402

from app.database.repositories.prediction_repository import (
    PredictionRepository,
)
from app.export.frames import (
    SUPPORTED_DATA_TYPES,
    TIMEFRAME_HOURS,
    build_btc_price_frame,
)

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
# A2.3 acceptance criterion: "High resolution (300 DPI)".
CHART_DPI = 300

# Figure size in inches. At 300 DPI this is 3600 × 1800 px, which
# is a comfortable print resolution without being wasteful.
CHART_FIGSIZE_INCHES = (12.0, 6.0)

# The data-source label that appears in the footer. Kept here so
# A2.5 can override it when the full metadata block lands.
CHART_DATA_SOURCE = "BTC price: btc_prices (Data Ingestion Service)"


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
    """

    file_name: str
    file_size: int
    timeframe: str
    rows_plotted: int
    content: bytes

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable dict.

        ``content`` is deliberately omitted — it can be large, and
        the caller already holds it.
        """
        return {
            "file_name": self.file_name,
            "file_size": self.file_size,
            "timeframe": self.timeframe,
            "rows_plotted": self.rows_plotted,
        }

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
            3. Plot: one line, legend, axis labels, title, footer.
            4. Save to a 300 DPI PNG byte buffer.

        Args:
            request: The chart request.

        Returns:
            ChartResult with the PNG bytes.

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

        # ---- 3. Plot ----
        content = self._render_png(
            frame=frame,
            timeframe=request.timeframe,
            title=request.title,
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
        )

    # ============================================================
    # RENDERING
    # ============================================================
    @staticmethod
    def _render_png(
        frame: pd.DataFrame,
        timeframe: str,
        title: Optional[str],
    ) -> bytes:
        """Render the frame to PNG bytes.

        The figure is always closed in a ``finally`` block so a
        long-running process does not accumulate figures.

        Args:
            frame: A frame from ``frames.build_btc_price_frame``.
                Must have ``time`` and ``close`` columns.
            timeframe: The timeframe label, used in the default
                title and the footer.
            title: Optional title override.

        Returns:
            PNG bytes.
        """
        # The frame's ``time`` column has already been stringified
        # by ``frames.stringify_timestamps``. Parse it back to
        # datetimes so matplotlib can lay out the x-axis sensibly.
        times = pd.to_datetime(frame["time"], utc=True)
        closes = frame["close"].astype(float).tolist()

        fig, ax = plt.subplots(
            figsize=CHART_FIGSIZE_INCHES,
            dpi=CHART_DPI,
        )

        try:
            ax.plot(
                times,
                closes,
                label="BTC close",
                linewidth=1.5,
                color="#1f77b4",
            )

            ax.set_xlabel("Time (UTC)")
            ax.set_ylabel("Price (USD)")
            ax.set_title(
                title if title else f"BTC price — {timeframe}"
            )
            ax.legend(loc="best")
            ax.grid(True, alpha=0.3)

            # Rotate the x tick labels so the dense timestamps
            # do not overlap on the 30d/90d charts.
            fig.autofmt_xdate(rotation=30)

            # Footer line: data source + render time. A2.5 will
            # replace this with a structured citations block.
            render_time = datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M UTC"
            )
            fig.text(
                0.01,
                0.01,
                f"Source: {CHART_DATA_SOURCE} | Rendered: {render_time}",
                fontsize=8,
                color="#555555",
            )

            # Reserve the bottom margin for the footer.
            fig.tight_layout(rect=(0.0, 0.03, 1.0, 1.0))

            buf = io.BytesIO()
            fig.savefig(
                buf,
                format="png",
                dpi=CHART_DPI,
                bbox_inches="tight",
            )
            return buf.getvalue()
        finally:
            plt.close(fig)

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
    "CHART_DPI",
    "CHART_DATA_SOURCE",
    "CHART_FIGSIZE_INCHES",
    "ChartRequest",
    "ChartResult",
    "PngExporter",
]