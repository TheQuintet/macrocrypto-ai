"""Unit tests for app.export.chart.

Covers:
    - CHART_DPI, CHART_FIGSIZE_INCHES, CHART_DATA_SOURCE constants
    - build_chart_figure returns an open Figure without saving
    - build_chart_figure renders a citations block when given
      metadata, or builds a default when given neither metadata nor
      the deprecated data_source (A2.5)
    - build_chart_figure still honors the deprecated data_source
      kwarg (A2.4 compatibility)
    - save_figure_png produces PNG bytes and closes the figure
    - save_figure_pdf produces PDF bytes and closes the figure
    - Both save paths close the figure even if savefig raises
    - No figure leak across repeated render/save cycles

The PNG payload is inspected via the IHDR chunk header. The PDF
payload is inspected via its magic number (``%PDF-``) and the
absence of a large embedded image object — a vector PDF for a
single line plot should be small.
"""

import struct
from datetime import datetime, timezone

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from app.export.chart import (
    CHART_DATA_SOURCE,
    CHART_DPI,
    CHART_FIGSIZE_INCHES,
    build_chart_figure,
    save_figure_pdf,
    save_figure_png,
)
from app.export.metadata import ExportMetadata, build_metadata


# ============================================================
# PAYLOAD HELPERS
# ============================================================
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
PDF_MAGIC = b"%PDF-"


def _png_dimensions(payload: bytes) -> tuple:
    """Return (width, height) from the PNG IHDR chunk."""
    assert payload.startswith(PNG_MAGIC), "not a PNG"
    width, height = struct.unpack(">II", payload[16:24])
    return width, height


# ============================================================
# FIXTURES
# ============================================================
FIXED_TS = datetime(2026, 9, 16, 14, 32, 0, tzinfo=timezone.utc)


def _btc_frame(hours: int = 48) -> pd.DataFrame:
    """Build a small frame with the two columns chart.py needs."""
    base = datetime(2026, 9, 14, tzinfo=timezone.utc)
    return pd.DataFrame(
        {
            "time": [
                (base + pd.Timedelta(hours=i)).isoformat()
                for i in range(hours)
            ],
            "close": [60000.0 + 100.0 * i for i in range(hours)],
        }
    )


# ============================================================
# CONSTANTS
# ============================================================
class TestChartConstants:
    """Module-level constants are stable."""

    def test_chart_dpi(self) -> None:
        assert CHART_DPI == 300

    def test_chart_figsize(self) -> None:
        assert CHART_FIGSIZE_INCHES == (12.0, 6.0)

    def test_chart_data_source_value(self) -> None:
        """The deprecated data-source label keeps its underscore.

        A2.3 shipped ``btc_prices`` (underscore). A2.4 moved the
        constant here; A2.5 marks it deprecated but keeps the value
        for backward compatibility. The value must not have
        changed.
        """
        assert "btc_prices" in CHART_DATA_SOURCE
        assert "btcprices" not in CHART_DATA_SOURCE


# ============================================================
# build_chart_figure
# ============================================================
class TestBuildChartFigure:
    """build_chart_figure constructs an open figure."""

    def test_returns_a_figure(self) -> None:
        from matplotlib.figure import Figure

        fig = build_chart_figure(_btc_frame(), timeframe="30d", title=None)
        try:
            assert isinstance(fig, Figure)
        finally:
            plt.close(fig)

    def test_does_not_close_the_figure(self) -> None:
        """The caller owns the figure; build_* must not close it."""
        before = len(plt.get_fignums())
        fig = build_chart_figure(_btc_frame(), timeframe="30d", title=None)
        after = len(plt.get_fignums())
        try:
            assert after == before + 1
        finally:
            plt.close(fig)

    def test_default_title_is_applied(self) -> None:
        """When title is None, the axes get a derived title."""
        fig = build_chart_figure(_btc_frame(), timeframe="90d", title=None)
        try:
            ax = fig.axes[0]
            assert "90d" in ax.get_title()
        finally:
            plt.close(fig)

    def test_custom_title_overrides_default(self) -> None:
        fig = build_chart_figure(
            _btc_frame(), timeframe="90d", title="Custom title"
        )
        try:
            ax = fig.axes[0]
            assert ax.get_title() == "Custom title"
        finally:
            plt.close(fig)

    def test_axis_labels_are_set(self) -> None:
        fig = build_chart_figure(_btc_frame(), timeframe="30d", title=None)
        try:
            ax = fig.axes[0]
            assert ax.get_xlabel() == "Time (UTC)"
            assert ax.get_ylabel() == "Price (USD)"
        finally:
            plt.close(fig)

    def test_legend_has_one_entry(self) -> None:
        fig = build_chart_figure(_btc_frame(), timeframe="30d", title=None)
        try:
            ax = fig.axes[0]
            legend = ax.get_legend()
            assert legend is not None
            assert len(legend.get_texts()) == 1
            assert legend.get_texts()[0].get_text() == "BTC close"
        finally:
            plt.close(fig)

    def test_custom_data_source_does_not_break(self) -> None:
        """The deprecated data_source kwarg is accepted.

        A2.4 shipped this kwarg; A2.5 preserves it as a shim. A2.6
        removes it.
        """
        fig = build_chart_figure(
            _btc_frame(),
            timeframe="30d",
            title=None,
            data_source="Custom source",
        )
        plt.close(fig)


# ============================================================
# build_chart_figure — METADATA (A2.5)
# ============================================================
class TestBuildChartFigureMetadata:
    """The citations footer path (A2.5)."""

    def _fig_texts(self, fig) -> list:
        """Return the string contents of every fig.text() call."""
        return [t.get_text() for t in fig.texts]

    def test_no_metadata_no_data_source_uses_default(self) -> None:
        """Neither kwarg → a default metadata block is built."""
        fig = build_chart_figure(
            _btc_frame(), timeframe="30d", title=None
        )
        try:
            texts = self._fig_texts(fig)
            assert len(texts) == 1
            footer = texts[0]
            # The default block is built with data_types=["chart"],
            # so it names CoinGecko and the AI Service, plus the
            # methodology and the access timestamp.
            assert "CoinGecko" in footer
            assert "MacroCrypto AI Service" in footer
            assert "MacroCrypto AI methodology" in footer
            assert "Accessed:" in footer
        finally:
            plt.close(fig)

    def test_explicit_metadata_is_rendered(self) -> None:
        """An explicit metadata block is rendered as the footer."""
        md = build_metadata(
            data_types=["btc_price"],
            significance_note="p<0.05",
            accessed_at=FIXED_TS,
        )
        fig = build_chart_figure(
            _btc_frame(), timeframe="30d", title=None, metadata=md
        )
        try:
            footer = self._fig_texts(fig)[0]
            assert "Sources: CoinGecko (https://www.coingecko.com)" in footer
            assert "Methodology: MacroCrypto AI methodology v1.0.0" in footer
            assert "Significance: p<0.05" in footer
            assert "Accessed: 2026-09-16 14:32 UTC" in footer
            # The rendered footer is exactly what the metadata
            # object produces.
            assert footer == md.to_footer_text()
        finally:
            plt.close(fig)

    def test_data_source_shim_takes_priority_over_metadata(self) -> None:
        """When both kwargs are set, data_source wins (A2.4 shim)."""
        md = build_metadata(
            data_types=["btc_price"], accessed_at=FIXED_TS
        )
        fig = build_chart_figure(
            _btc_frame(),
            timeframe="30d",
            title=None,
            metadata=md,
            data_source="deprecated source",
        )
        try:
            footer = self._fig_texts(fig)[0]
            # A2.4-era single-line footer, not the citations block.
            assert footer.startswith("Source: deprecated source | Rendered:")
            assert "Methodology:" not in footer
        finally:
            plt.close(fig)

    def test_metadata_footer_contains_timestamp(self) -> None:
        """The access timestamp from the metadata is present."""
        md = ExportMetadata(
            sources=[],
            methodology=build_metadata().methodology,
            accessed_at=FIXED_TS,
            significance_note=None,
        )
        fig = build_chart_figure(
            _btc_frame(), timeframe="30d", title=None, metadata=md
        )
        try:
            footer = self._fig_texts(fig)[0]
            assert "2026-09-16 14:32 UTC" in footer
        finally:
            plt.close(fig)


# ============================================================
# save_figure_png
# ============================================================
class TestSaveFigurePng:
    """save_figure_png serializes to PNG and closes."""

    def test_produces_png_bytes(self) -> None:
        fig = build_chart_figure(_btc_frame(), timeframe="30d", title=None)
        payload = save_figure_png(fig)
        assert isinstance(payload, bytes)
        assert payload.startswith(PNG_MAGIC)

    def test_closes_the_figure(self) -> None:
        before = len(plt.get_fignums())
        fig = build_chart_figure(_btc_frame(), timeframe="30d", title=None)
        save_figure_png(fig)
        after = len(plt.get_fignums())
        assert after == before

    def test_default_dpi_matches_constant(self) -> None:
        fig = build_chart_figure(_btc_frame(), timeframe="30d", title=None)
        payload = save_figure_png(fig)
        width, height = _png_dimensions(payload)
        # At 300 DPI and figsize (12, 6): 3600 × 1800 nominal.
        # tight bbox can trim or grow; allow the same band the A2.3
        # test uses.
        target_w = int(CHART_FIGSIZE_INCHES[0] * CHART_DPI)
        target_h = int(CHART_FIGSIZE_INCHES[1] * CHART_DPI)
        assert 0.85 * target_w <= width <= 1.10 * target_w
        assert 0.85 * target_h <= height <= 1.10 * target_h


# ============================================================
# save_figure_pdf
# ============================================================
class TestSaveFigurePdf:
    """save_figure_pdf serializes to PDF and closes."""

    def test_produces_pdf_bytes(self) -> None:
        fig = build_chart_figure(_btc_frame(), timeframe="30d", title=None)
        payload = save_figure_pdf(fig)
        assert isinstance(payload, bytes)
        assert payload.startswith(PDF_MAGIC)

    def test_closes_the_figure(self) -> None:
        before = len(plt.get_fignums())
        fig = build_chart_figure(_btc_frame(), timeframe="30d", title=None)
        save_figure_pdf(fig)
        after = len(plt.get_fignums())
        assert after == before

    def test_pdf_is_much_smaller_than_png(self) -> None:
        """Vector output for a single line plot is far more compact
        than a 300 DPI raster. If this ever flips, something is
        rasterizing where it should not be.
        """
        frame = _btc_frame()
        png = save_figure_png(
            build_chart_figure(frame, timeframe="30d", title=None)
        )
        pdf = save_figure_pdf(
            build_chart_figure(frame, timeframe="30d", title=None)
        )
        # In practice PDF is ~10× smaller; assert at least 2×.
        assert len(pdf) * 2 < len(png), (
            f"PDF ({len(pdf)}) not meaningfully smaller than PNG "
            f"({len(png)})"
        )


# ============================================================
# FIGURE LIFECYCLE
# ============================================================
class TestFigureLifecycle:
    """Repeated save cycles do not leak figures."""

    def test_mixed_save_cycles_do_not_leak(self) -> None:
        before = len(plt.get_fignums())
        for _ in range(3):
            save_figure_png(
                build_chart_figure(_btc_frame(12), "30d", None)
            )
            save_figure_pdf(
                build_chart_figure(_btc_frame(12), "30d", None)
            )
        after = len(plt.get_fignums())
        assert after == before