"""Unit tests for app.export.png_export.

Covers:
    - CHART_DPI, CHART_FIGSIZE_INCHES, CHART_DATA_SOURCE constants
    - ChartRequest / ChartResult dataclasses (to_dict, __repr__)
    - PngExporter._filename for every timeframe
    - PngExporter.render against a fake repository:
        - happy path: PNG bytes, non-empty, correct magic number
        - PNG dimensions match CHART_DPI × CHART_FIGSIZE_INCHES
        - the 300 DPI assertion (PNG pHYs chunk carries it)
        - title override path vs. default title path
        - empty frame raises ValueError
        - unknown timeframe raises ValueError
    - _render_png closes the figure (no pyplot leak)

The PNG payload is inspected directly via its byte header and via
Pillow-free parsing of the PNG IHDR/pHYs chunks. matplotlib is
already a dependency; we do not add Pillow for this.
"""

import io
import struct
from datetime import datetime, timezone
from typing import Any, List, Optional

import pandas as pd
import pytest

from app.export.png_export import (
    CHART_DATA_SOURCE,
    CHART_DPI,
    CHART_FIGSIZE_INCHES,
    ChartRequest,
    ChartResult,
    PngExporter,
)


# ============================================================
# PNG PARSING HELPERS
# ============================================================
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _png_dimensions(payload: bytes) -> tuple:
    """Return (width, height) from the PNG's IHDR chunk.

    Reads the first chunk header after the 8-byte PNG signature.
    The IHDR chunk is defined by the PNG spec to be first, and its
    data is width (4 bytes BE) then height (4 bytes BE).
    """
    assert payload.startswith(PNG_MAGIC), "not a PNG"
    # Bytes 8..11: length; 12..15: type ("IHDR"); 16..19: width;
    # 20..23: height. All big-endian.
    width, height = struct.unpack(">II", payload[16:24])
    return width, height


def _png_phys_dpi(payload: bytes) -> Optional[tuple]:
    """Return (x_ppi, y_ppi) from the PNG's pHYs chunk, if present.

    The pHYs chunk stores pixels per unit and a unit specifier
    (0=unknown, 1=metre). matplotlib writes unit=1, so we convert
    pixels-per-metre to pixels-per-inch by dividing by 39.3701.
    """
    assert payload.startswith(PNG_MAGIC), "not a PNG"
    offset = 8
    while offset < len(payload):
        length = struct.unpack(">I", payload[offset : offset + 4])[0]
        chunk_type = payload[offset + 4 : offset + 8]
        data_start = offset + 8
        data_end = data_start + length

        if chunk_type == b"pHYs":
            x_ppm, y_ppm, unit = struct.unpack(
                ">IIB", payload[data_start : data_start + 9]
            )
            if unit != 1:
                return None
            # pixels per metre → pixels per inch
            return (
                round(x_ppm / 39.3701, 0),
                round(y_ppm / 39.3701, 0),
            )
        if chunk_type == b"IEND":
            break
        offset = data_end + 4  # skip CRC

    return None


# ============================================================
# FAKE REPOSITORY
# ============================================================
class _FakePredictionRepo:
    """Returns a canned BTC price DataFrame for PngExporter tests."""

    def __init__(self, btc: Optional[pd.DataFrame] = None) -> None:
        self._btc = btc if btc is not None else pd.DataFrame()
        self.calls: List[int] = []

    async def fetch_recent_btc_data(self, hours: int) -> pd.DataFrame:
        self.calls.append(hours)
        return self._btc.copy()


# ============================================================
# FIXTURES
# ============================================================
def _btc_frame(hours: int = 48) -> pd.DataFrame:
    """Build a small ascending BTC frame matching the repo shape.

    The frame carries every column the shared
    ``build_btc_price_frame`` expects, but only ``time`` and
    ``close`` matter for the PNG exporter.
    """
    base = datetime(2026, 9, 14, tzinfo=timezone.utc)
    return pd.DataFrame(
        {
            "time": [base + pd.Timedelta(hours=i) for i in range(hours)],
            "close": [60000.0 + 100.0 * i for i in range(hours)],
            "volume": [1000.0] * hours,
            "volatility": [0.02] * hours,
            "dominance": [0.55] * hours,
            "active_addresses": [500_000] * hours,
            "price_lag_7d": [59000.0] * hours,
        }
    )


# ============================================================
# CONSTANTS
# ============================================================
class TestPngConstants:
    """Module-level constants are stable."""

    def test_chart_dpi(self) -> None:
        assert CHART_DPI == 300

    def test_chart_figsize(self) -> None:
        assert CHART_FIGSIZE_INCHES == (12.0, 6.0)

    def test_chart_data_source_present(self) -> None:
        assert isinstance(CHART_DATA_SOURCE, str)
        assert CHART_DATA_SOURCE.strip() != ""


# ============================================================
# DATACLASSES
# ============================================================
class TestChartRequest:
    """ChartRequest defaults, to_dict, and __repr__."""

    def test_defaults(self) -> None:
        req = ChartRequest()
        assert req.timeframe == "30d"
        assert req.user_id is None
        assert req.title is None

    def test_to_dict_round_trip(self) -> None:
        req = ChartRequest(
            timeframe="90d", user_id="analyst-42", title="My chart"
        )
        assert req.to_dict() == {
            "timeframe": "90d",
            "user_id": "analyst-42",
            "title": "My chart",
        }

    def test_repr_contains_key_fields(self) -> None:
        text = repr(ChartRequest(timeframe="1y", user_id="u-1"))
        assert "1y" in text
        assert "u-1" in text


class TestChartResult:
    """ChartResult to_dict and __repr__."""

    def test_to_dict_omits_content(self) -> None:
        res = ChartResult(
            file_name="f.png",
            file_size=100,
            timeframe="30d",
            rows_plotted=10,
            content=b"fakepng",
        )
        d = res.to_dict()
        assert "content" not in d
        assert d == {
            "file_name": "f.png",
            "file_size": 100,
            "timeframe": "30d",
            "rows_plotted": 10,
        }

    def test_repr_contains_key_fields(self) -> None:
        res = ChartResult(
            file_name="f.png",
            file_size=100,
            timeframe="30d",
            rows_plotted=10,
            content=b"",
        )
        text = repr(res)
        assert "f.png" in text
        assert "30d" in text
        assert "10" in text


# ============================================================
# FILENAME
# ============================================================
class TestFilename:
    """PngExporter._filename matches the A2.3 naming convention."""

    def test_single_timeframe_30d(self) -> None:
        name = PngExporter._filename("30d")
        assert name.startswith("macro-crypto-chart-30d-")
        assert name.endswith(".png")

    def test_all_timeframes(self) -> None:
        for tf in ("30d", "90d", "1y", "5y"):
            name = PngExporter._filename(tf)
            assert name.startswith(f"macro-crypto-chart-{tf}-")
            assert name.endswith(".png")

    def test_date_is_utc_iso(self) -> None:
        name = PngExporter._filename("30d")
        # macro-crypto-chart-30d-YYYY-MM-DD.png
        parts = name[:-4].split("-")
        assert len(parts[-3]) == 4  # year
        assert len(parts[-2]) == 2  # month
        assert len(parts[-1]) == 2  # day


# ============================================================
# render() — VALIDATION
# ============================================================
class TestRenderValidation:
    """render() rejects bad requests before doing any work."""

    @pytest.mark.asyncio
    async def test_unknown_timeframe(self) -> None:
        exporter = PngExporter(_FakePredictionRepo())
        with pytest.raises(ValueError, match="Unknown timeframe"):
            await exporter.render(ChartRequest(timeframe="1m"))

    @pytest.mark.asyncio
    async def test_empty_frame_raises(self) -> None:
        repo = _FakePredictionRepo(btc=pd.DataFrame())
        exporter = PngExporter(repo)
        with pytest.raises(ValueError, match="zero rows"):
            await exporter.render(ChartRequest(timeframe="30d"))

    @pytest.mark.asyncio
    async def test_bad_timeframe_does_not_touch_repo(self) -> None:
        repo = _FakePredictionRepo(btc=_btc_frame(3))
        exporter = PngExporter(repo)
        with pytest.raises(ValueError):
            await exporter.render(ChartRequest(timeframe="1m"))
        assert repo.calls == []


# ============================================================
# render() — HAPPY PATH
# ============================================================
class TestRenderHappyPath:
    """render() produces a well-formed PNG."""

    @pytest.mark.asyncio
    async def test_returns_chart_result(self) -> None:
        repo = _FakePredictionRepo(btc=_btc_frame(48))
        exporter = PngExporter(repo)
        result = await exporter.render(ChartRequest(timeframe="30d"))
        assert isinstance(result, ChartResult)
        assert result.rows_plotted == 48
        assert result.timeframe == "30d"
        assert result.file_size == len(result.content)
        assert result.file_size > 0

    @pytest.mark.asyncio
    async def test_png_magic_number(self) -> None:
        repo = _FakePredictionRepo(btc=_btc_frame(12))
        exporter = PngExporter(repo)
        result = await exporter.render(ChartRequest(timeframe="30d"))
        assert result.content.startswith(PNG_MAGIC)

    @pytest.mark.asyncio
    async def test_filename_convention(self) -> None:
        repo = _FakePredictionRepo(btc=_btc_frame(12))
        exporter = PngExporter(repo)
        result = await exporter.render(ChartRequest(timeframe="90d"))
        assert result.file_name.startswith("macro-crypto-chart-90d-")
        assert result.file_name.endswith(".png")

    @pytest.mark.asyncio
    async def test_repo_receives_correct_hours(self) -> None:
        repo = _FakePredictionRepo(btc=_btc_frame(12))
        exporter = PngExporter(repo)
        await exporter.render(ChartRequest(timeframe="30d"))
        # 30d → 720 hours
        assert repo.calls == [720]

    @pytest.mark.asyncio
    async def test_repo_receives_hours_for_every_timeframe(self) -> None:
        for tf, expected_hours in (
            ("30d", 720),
            ("90d", 2160),
            ("1y", 8760),
            ("5y", 43800),
        ):
            repo = _FakePredictionRepo(btc=_btc_frame(6))
            exporter = PngExporter(repo)
            await exporter.render(ChartRequest(timeframe=tf))
            assert repo.calls == [expected_hours], tf


# ============================================================
# render() — RESOLUTION
# ============================================================
class TestRenderResolution:
    """The rendered PNG reports 300 DPI."""

    @pytest.mark.asyncio
    async def test_png_dimensions_match_dpi_and_figsize(self) -> None:
        """Pixel dimensions are in a sensible band around figsize × DPI.

        12.0 inches × 300 DPI = 3600 px width
        6.0 inches × 300 DPI  = 1800 px height

        matplotlib's ``bbox_inches="tight"`` trims whitespace from
        the figure, but it can also *expand* the canvas to include
        anything drawn outside the axes — the title above, the
        x-axis tick labels below, and the footer text. The band
        below allows for both directions: down to 85% of target
        (trimming) and up to 110% of target (growth). The hard
        resolution check lives in
        ``test_png_phys_chunk_reports_300_dpi``; this test is a
        sanity band on the pixel count.
        """
        repo = _FakePredictionRepo(btc=_btc_frame(12))
        exporter = PngExporter(repo)
        result = await exporter.render(ChartRequest(timeframe="30d"))

        width, height = _png_dimensions(result.content)
        target_w = int(CHART_FIGSIZE_INCHES[0] * CHART_DPI)  # 3600
        target_h = int(CHART_FIGSIZE_INCHES[1] * CHART_DPI)  # 1800

        # bbox_inches="tight" can trim up to ~15% or grow up to
        # ~10% depending on where the decorations land.
        assert 0.85 * target_w <= width <= 1.10 * target_w, (
            f"width {width} outside "
            f"[{int(0.85 * target_w)}, {int(1.10 * target_w)}]"
        )
        assert 0.85 * target_h <= height <= 1.10 * target_h, (
            f"height {height} outside "
            f"[{int(0.85 * target_h)}, {int(1.10 * target_h)}]"
        )

    @pytest.mark.asyncio
    async def test_png_phys_chunk_reports_300_dpi(self) -> None:
        """The PNG pHYs chunk carries the 300 DPI resolution.

        matplotlib writes a pHYs chunk by default. If this ever
        changes, the assertion below becomes the canary.
        """
        repo = _FakePredictionRepo(btc=_btc_frame(12))
        exporter = PngExporter(repo)
        result = await exporter.render(ChartRequest(timeframe="30d"))

        dpi = _png_phys_dpi(result.content)
        # The pHYs chunk is optional in the PNG spec, but
        # matplotlib always writes it. If it disappears, this test
        # fails loudly and we revisit the resolution assertion.
        assert dpi is not None, "PNG does not contain a pHYs chunk"
        x_ppi, y_ppi = dpi
        assert abs(x_ppi - 300) <= 2
        assert abs(y_ppi - 300) <= 2


# ============================================================
# render() — TITLE OVERRIDE
# ============================================================
class TestRenderTitle:
    """The title override is passed through to _render_png."""

    @pytest.mark.asyncio
    async def test_default_title_path(self) -> None:
        """Calling without a title exercises the default-title branch."""
        repo = _FakePredictionRepo(btc=_btc_frame(12))
        exporter = PngExporter(repo)
        result = await exporter.render(
            ChartRequest(timeframe="30d", title=None)
        )
        # No assertion on the title text — it lives in the PNG
        # pixels, not the byte header. The test exists to exercise
        # the None branch for coverage.
        assert result.rows_plotted == 12

    @pytest.mark.asyncio
    async def test_custom_title_path(self) -> None:
        """Calling with a title exercises the override branch."""
        repo = _FakePredictionRepo(btc=_btc_frame(12))
        exporter = PngExporter(repo)
        result = await exporter.render(
            ChartRequest(timeframe="30d", title="Custom title")
        )
        assert result.rows_plotted == 12


# ============================================================
# RENDERER — FIGURE LIFECYCLE
# ============================================================
class TestRenderFigureLifecycle:
    """_render_png closes the figure it opens."""

    def test_figure_count_unchanged_after_render(self) -> None:
        """After rendering, pyplot's open-figure set is unchanged.

        If _render_png forgot its ``plt.close(fig)`` in the finally
        block, this count would climb.
        """
        import matplotlib.pyplot as plt

        before = len(plt.get_fignums())

        frame = _btc_frame(12)
        PngExporter._render_png(
            frame=frame,
            timeframe="30d",
            title=None,
        )

        after = len(plt.get_fignums())
        assert after == before

    def test_render_does_not_raise_on_long_frame(self) -> None:
        """A long frame (5y = 43800 hours would be huge in prod) is
        still rendered without error at a modest size.

        We use 500 hours so the test is fast; the point is that
        larger frames do not break the renderer.
        """
        frame = _btc_frame(500)
        payload = PngExporter._render_png(
            frame=frame,
            timeframe="1y",
            title=None,
        )
        assert payload.startswith(PNG_MAGIC)