"""PDF chart export generation for analyst-facing downloads (A2.4).

Renders a single-page, vector-quality PDF containing the same BTC
price chart the PNG exporter (A2.3) produces: one close-price line
over the export window, legend, axis labels, title, and a footer
line naming the data source and the render time.

The output is true vector PDF — every plot element is emitted as a
PDF drawing operation, not rasterized. This is the "vector quality"
the A2.4 acceptance criterion asks for.

Design:

    - Pure: reads via the injected ``PredictionRepository``,
      returns bytes. Does not write files, does not call the
      ``export_history`` repository, does not open its own DB
      session. The caller owns the session (see
      ``app.export.service``) and owns persistence.
    - The BTC price frame comes from
      ``app.export.frames.build_btc_price_frame`` — the same
      builder the CSV and PNG exporters use. One fetch path for
      the A2 ticket family.
    - The Figure construction and the PDF save step live in
      ``app.export.chart``, shared with the PNG exporter. This
      module stays a thin format-specific wrapper.
    - matplotlib's PDF backend produces the vector output. No
      additional dependency is required for the single-page chart;
      ``reportlab`` is only needed for multi-page report assembly,
      which is out of scope for this branch (see the A2.4 ticket's
      follow-up note).

File naming follows the A2.4 criterion exactly:

    macro-crypto-report-[timeframe]-[YYYY-MM-DD].pdf

Usage:

    async with session_scope() as session:
        exporter = PdfExporter(
            prediction_repo=PredictionRepository(session),
        )
        result = await exporter.render(
            PdfRequest(timeframe="90d", user_id="analyst-42")
        )
        # result.content is the PDF bytes
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
    build_chart_figure,
    save_figure_pdf,
)
from app.export.frames import (
    TIMEFRAME_HOURS,
    build_btc_price_frame,
)

logger = logging.getLogger(__name__)


# ============================================================
# REQUEST / RESULT DATACLASSES
# ============================================================
@dataclass
class PdfRequest:
    """A single PDF chart request.

    Same shape as ``ChartRequest`` from ``png_export``. Kept as a
    separate dataclass so the PDF path can grow its own fields
    (page size, orientation, whether to include a data table)
    without touching the PNG path's contract.

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
            f"PdfRequest(timeframe={self.timeframe!r}, "
            f"user_id={self.user_id!r})"
        )


@dataclass
class PdfResult:
    """The output of a PDF chart export.

    ``content`` is the PDF byte payload. The caller is responsible
    for persisting it (local disk or object store) and for
    recording the export in ``export_history``. Neither happens
    here.

    Attributes:
        file_name: The generated filename, following
            ``macro-crypto-report-[timeframe]-[YYYY-MM-DD].pdf``.
        file_size: ``len(content)`` in bytes.
        timeframe: The timeframe that was requested (echoed).
        rows_plotted: Number of BTC price rows that were plotted.
        pages: Page count of the produced PDF. Always 1 on this
            branch — the multi-page report assembler is out of
            scope. Kept as a field so a future branch can populate
            it without changing the public shape.
        content: The PDF bytes.
    """

    file_name: str
    file_size: int
    timeframe: str
    rows_plotted: int
    content: bytes
    pages: int = 1

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
            "pages": self.pages,
        }

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"PdfResult(file_name={self.file_name!r}, "
            f"file_size={self.file_size}, "
            f"timeframe={self.timeframe!r}, "
            f"rows_plotted={self.rows_plotted}, "
            f"pages={self.pages})"
        )


# ============================================================
# EXPORTER
# ============================================================
class PdfExporter:
    """Render a single-page PDF chart from the BTC price series.

    The exporter reads via the injected repository and returns
    bytes. It does not open a session, does not write files, and
    does not record the export in ``export_history``. Those are
    the caller's responsibilities (see ``app.export.service``).

    Example:
        exporter = PdfExporter(prediction_repo)
        result = await exporter.render(
            PdfRequest(timeframe="90d", user_id="analyst-42")
        )
        # result.content is the PDF bytes
    """

    def __init__(
        self,
        prediction_repo: PredictionRepository,
    ) -> None:
        """Initialize the exporter.

        Args:
            prediction_repo: Reads BTC price rows from the source
                tables. The same repository the CSV and PNG
                exporters use.
        """
        self._prediction_repo = prediction_repo

    # ============================================================
    # PUBLIC API
    # ============================================================
    async def render(self, request: PdfRequest) -> PdfResult:
        """Render a PDF chart for the given request.

        Steps:
            1. Validate the timeframe.
            2. Build the BTC price frame via the shared
               ``frames.build_btc_price_frame``.
            3. Build the Figure via ``chart.build_chart_figure``.
            4. Save to a vector PDF byte buffer via
               ``chart.save_figure_pdf``.

        Args:
            request: The PDF request.

        Returns:
            PdfResult with the PDF bytes.

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
            f"Building PDF chart: timeframe={request.timeframe} "
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

        # ---- 3. Build the Figure, then save ----
        content = self._render_pdf(
            frame=frame,
            timeframe=request.timeframe,
            title=request.title,
        )

        file_name = self._filename(timeframe=request.timeframe)
        rows_plotted = len(frame)

        logger.info(
            f"Built PDF chart: {file_name} "
            f"({rows_plotted} rows, {len(content)} bytes)"
        )

        return PdfResult(
            file_name=file_name,
            file_size=len(content),
            timeframe=request.timeframe,
            rows_plotted=rows_plotted,
            content=content,
            pages=1,
        )

    # ============================================================
    # RENDERING
    # ============================================================
    @staticmethod
    def _render_pdf(
        frame: pd.DataFrame,
        timeframe: str,
        title: Optional[str],
    ) -> bytes:
        """Render the frame to vector PDF bytes.

        Thin wrapper over ``chart.build_chart_figure`` +
        ``chart.save_figure_pdf``. The figure is closed inside
        ``save_figure_pdf``'s ``finally`` block, so no leak is
        possible even if ``savefig`` raises.

        Args:
            frame: A frame from ``frames.build_btc_price_frame``.
                Must have ``time`` and ``close`` columns.
            timeframe: The timeframe label, used in the default
                title and the footer.
            title: Optional title override.

        Returns:
            PDF bytes beginning with ``%PDF-``.
        """
        fig = build_chart_figure(
            frame=frame,
            timeframe=timeframe,
            title=title,
        )
        return save_figure_pdf(fig)

    @staticmethod
    def _filename(timeframe: str) -> str:
        """Generate the PDF filename.

        Follows the A2.4 criterion exactly:

            ``macro-crypto-report-<timeframe>-<YYYY-MM-DD>.pdf``

        The date is UTC.

        Args:
            timeframe: The requested timeframe.

        Returns:
            The filename string.
        """
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"macro-crypto-report-{timeframe}-{date_str}.pdf"


__all__ = [
    "PdfExporter",
    "PdfRequest",
    "PdfResult",
]