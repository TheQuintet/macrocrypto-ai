"""Shared chart construction and figure serialization.

Both export formats that render a chart — PNG (A2.3) and PDF
(A2.4) — build the same matplotlib Figure: one BTC close line over
the export window, legend, axis labels, a title, and a footer line
naming the data source and the render time.

This module is that figure, plus the two save paths:

    - ``save_figure_png(fig)`` — 300 DPI PNG bytes (pHYs chunk
      carries the resolution).
    - ``save_figure_pdf(fig)`` — vector PDF bytes.

Design:

    - Pure construction: ``build_chart_figure`` returns a Figure
      and does nothing else. It does not save, does not close, does
      not touch the filesystem. The caller owns the Figure's
      lifecycle.
    - Each ``save_figure_*`` function owns its own ``plt.close``
      in a ``finally`` block. After a save, the caller has nothing
      left to do with the figure, so leaving it open would leak.
    - The constants live here so both format-specific modules
      re-export the same values. ``png_export`` re-exports
      ``CHART_DPI``, ``CHART_FIGSIZE_INCHES``, and
      ``CHART_DATA_SOURCE`` for backward compatibility with A2.3's
      tests and callers.
    - The footnote ("Source: ... | Rendered: ...") is applied here
      rather than in the format modules because A2.5 will replace
      it with a structured citations block in exactly one place.
      The ``data_source`` parameter is what A2.5 will override.

Usage:

    from app.export.chart import (
        build_chart_figure,
        save_figure_png,
        save_figure_pdf,
    )

    fig = build_chart_figure(frame, timeframe="30d", title=None)
    png_bytes = save_figure_png(fig)   # closes fig

    fig = build_chart_figure(frame, timeframe="30d", title=None)
    pdf_bytes = save_figure_pdf(fig)   # closes fig
"""

import io
import logging
from datetime import datetime, timezone
from typing import Optional

import matplotlib

# Agg is the headless backend. It must be selected before pyplot
# is imported anywhere. Importing pyplot *after* use("Agg") is the
# documented-safe order.
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402  (after matplotlib.use)
import pandas as pd  # noqa: E402

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
# A2.3 acceptance criterion: "High resolution (300 DPI)".
CHART_DPI = 300

# Figure size in inches. At 300 DPI this is 3600 × 1800 px for the
# PNG path. For the PDF path, inches are the vector coordinate
# system; the same figsize produces a 12 × 6 inch page.
CHART_FIGSIZE_INCHES = (12.0, 6.0)

# The data-source label that appears in the footer. Kept here so
# A2.5 can override it when the full metadata block lands.
CHART_DATA_SOURCE = "BTC price: btc_prices (Data Ingestion Service)"


# ============================================================
# FIGURE CONSTRUCTION
# ============================================================
def build_chart_figure(
    frame: pd.DataFrame,
    timeframe: str,
    title: Optional[str],
    *,
    data_source: str = CHART_DATA_SOURCE,
):
    """Construct the chart Figure from a BTC price frame.

    The Figure is returned open and unsaved. The caller must save
    it via one of ``save_figure_png`` / ``save_figure_pdf``, both
    of which close the figure for you.

    Steps:

        - Parse the ISO-8601 ``time`` column back to datetimes.
        - Plot a single "BTC close" line.
        - Apply axis labels, title, legend, and grid.
        - Rotate the x tick labels (the dense timestamps on 30d
          and 90d windows would otherwise overlap).
        - Add the footer line (data source + render time).
        - Reserve the bottom margin so the footer is not clipped.

    Args:
        frame: A frame from ``frames.build_btc_price_frame``. Must
            have ``time`` and ``close`` columns.
        timeframe: The timeframe label, used in the default title.
        title: Optional title override. When None, a default title
            is derived from the timeframe.
        data_source: Footer source label. Defaults to the module
            constant; A2.5 will override it when the citations
            block lands.

    Returns:
        An open :class:`matplotlib.figure.Figure` instance.
    """
    # The frame's ``time`` column has already been stringified by
    # ``frames.stringify_timestamps``. Parse it back to datetimes
    # so matplotlib can lay out the x-axis sensibly.
    times = pd.to_datetime(frame["time"], utc=True)
    closes = frame["close"].astype(float).tolist()

    fig, ax = plt.subplots(
        figsize=CHART_FIGSIZE_INCHES,
        dpi=CHART_DPI,
    )

    ax.plot(
        times,
        closes,
        label="BTC close",
        linewidth=1.5,
        color="#1f77b4",
    )

    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel("Price (USD)")
    ax.set_title(title if title else f"BTC price — {timeframe}")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    # Rotate the x tick labels so the dense timestamps do not
    # overlap on the 30d / 90d charts.
    fig.autofmt_xdate(rotation=30)

    # Footer line: data source + render time. A2.5 will replace
    # this with a structured citations block.
    render_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    fig.text(
        0.01,
        0.01,
        f"Source: {data_source} | Rendered: {render_time}",
        fontsize=8,
        color="#555555",
    )

    # Reserve the bottom margin for the footer.
    fig.tight_layout(rect=(0.0, 0.03, 1.0, 1.0))

    return fig


# ============================================================
# SAVE PATHS
# ============================================================
def save_figure_png(fig, *, dpi: int = CHART_DPI) -> bytes:
    """Serialize a Figure to PNG bytes and close it.

    Args:
        fig: The Figure returned by :func:`build_chart_figure`.
        dpi: Output resolution. Defaults to ``CHART_DPI`` (300).

    Returns:
        PNG bytes. The pHYs chunk carries the resolution.
    """
    try:
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format="png",
            dpi=dpi,
            bbox_inches="tight",
        )
        return buf.getvalue()
    finally:
        plt.close(fig)


def save_figure_pdf(fig) -> bytes:
    """Serialize a Figure to vector PDF bytes and close it.

    The output is true vector PDF: the plot line, axes, labels,
    and text are all emitted as PDF drawing operations, not as a
    rasterized image. This is the "vector quality" the A2.4
    acceptance criterion asks for.

    Args:
        fig: The Figure returned by :func:`build_chart_figure`.

    Returns:
        PDF bytes. The payload begins with the PDF magic number
        ``%PDF-``.
    """
    try:
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format="pdf",
            bbox_inches="tight",
        )
        return buf.getvalue()
    finally:
        plt.close(fig)


__all__ = [
    "CHART_DATA_SOURCE",
    "CHART_DPI",
    "CHART_FIGSIZE_INCHES",
    "build_chart_figure",
    "save_figure_pdf",
    "save_figure_png",
]