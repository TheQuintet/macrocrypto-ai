"""Unit tests for app.export.pdf_export.

Covers:
    - PdfExporter._filename for every timeframe
    - PdfRequest / PdfResult dataclasses (to_dict, __repr__,
      pages default)
    - PdfExporter.render against a fake repository:
        - happy path: PDF bytes, correct magic number, pages=1
        - vector-quality signature (PDF is much smaller than the
          equivalent PNG)
        - title override path vs. default title path
        - empty frame raises ValueError
        - unknown timeframe raises ValueError
    - _render_pdf closes the figure (no pyplot leak)
"""

from datetime import datetime, timezone
from typing import List, Optional

import pandas as pd
import pytest

from app.export.pdf_export import (
    PdfExporter,
    PdfRequest,
    PdfResult,
)


PDF_MAGIC = b"%PDF-"


# ============================================================
# FAKE REPOSITORY
# ============================================================
class _FakePredictionRepo:
    """Returns a canned BTC price DataFrame for PdfExporter tests."""

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
    """Build a small ascending BTC frame matching the repo shape."""
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
# DATACLASSES
# ============================================================
class TestPdfRequest:
    """PdfRequest defaults, to_dict, and __repr__."""

    def test_defaults(self) -> None:
        req = PdfRequest()
        assert req.timeframe == "30d"
        assert req.user_id is None
        assert req.title is None

    def test_to_dict_round_trip(self) -> None:
        req = PdfRequest(
            timeframe="90d", user_id="analyst-42", title="My report"
        )
        assert req.to_dict() == {
            "timeframe": "90d",
            "user_id": "analyst-42",
            "title": "My report",
        }

    def test_repr_contains_key_fields(self) -> None:
        text = repr(PdfRequest(timeframe="1y", user_id="u-1"))
        assert "1y" in text
        assert "u-1" in text


class TestPdfResult:
    """PdfResult to_dict, __repr__, and pages default."""

    def test_pages_defaults_to_one(self) -> None:
        res = PdfResult(
            file_name="f.pdf",
            file_size=100,
            timeframe="30d",
            rows_plotted=10,
            content=b"%PDF-",
        )
        assert res.pages == 1

    def test_to_dict_includes_pages_omits_content(self) -> None:
        res = PdfResult(
            file_name="f.pdf",
            file_size=100,
            timeframe="30d",
            rows_plotted=10,
            content=b"%PDF-",
            pages=1,
        )
        d = res.to_dict()
        assert "content" not in d
        assert d == {
            "file_name": "f.pdf",
            "file_size": 100,
            "timeframe": "30d",
            "rows_plotted": 10,
            "pages": 1,
        }

    def test_repr_contains_key_fields(self) -> None:
        res = PdfResult(
            file_name="f.pdf",
            file_size=100,
            timeframe="30d",
            rows_plotted=10,
            content=b"",
        )
        text = repr(res)
        assert "f.pdf" in text
        assert "30d" in text
        assert "10" in text


# ============================================================
# FILENAME
# ============================================================
class TestFilename:
    """PdfExporter._filename matches the A2.4 naming convention."""

    def test_single_timeframe_30d(self) -> None:
        name = PdfExporter._filename("30d")
        assert name.startswith("macro-crypto-report-30d-")
        assert name.endswith(".pdf")

    def test_all_timeframes(self) -> None:
        for tf in ("30d", "90d", "1y", "5y"):
            name = PdfExporter._filename(tf)
            assert name.startswith(f"macro-crypto-report-{tf}-")
            assert name.endswith(".pdf")

    def test_date_is_utc_iso(self) -> None:
        name = PdfExporter._filename("30d")
        # macro-crypto-report-30d-YYYY-MM-DD.pdf
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
        exporter = PdfExporter(_FakePredictionRepo())
        with pytest.raises(ValueError, match="Unknown timeframe"):
            await exporter.render(PdfRequest(timeframe="1m"))

    @pytest.mark.asyncio
    async def test_empty_frame_raises(self) -> None:
        repo = _FakePredictionRepo(btc=pd.DataFrame())
        exporter = PdfExporter(repo)
        with pytest.raises(ValueError, match="zero rows"):
            await exporter.render(PdfRequest(timeframe="30d"))

    @pytest.mark.asyncio
    async def test_bad_timeframe_does_not_touch_repo(self) -> None:
        repo = _FakePredictionRepo(btc=_btc_frame(3))
        exporter = PdfExporter(repo)
        with pytest.raises(ValueError):
            await exporter.render(PdfRequest(timeframe="1m"))
        assert repo.calls == []


# ============================================================
# render() — HAPPY PATH
# ============================================================
class TestRenderHappyPath:
    """render() produces a well-formed PDF."""

    @pytest.mark.asyncio
    async def test_returns_pdf_result(self) -> None:
        repo = _FakePredictionRepo(btc=_btc_frame(48))
        exporter = PdfExporter(repo)
        result = await exporter.render(PdfRequest(timeframe="30d"))
        assert isinstance(result, PdfResult)
        assert result.rows_plotted == 48
        assert result.timeframe == "30d"
        assert result.pages == 1
        assert result.file_size == len(result.content)
        assert result.file_size > 0

    @pytest.mark.asyncio
    async def test_pdf_magic_number(self) -> None:
        repo = _FakePredictionRepo(btc=_btc_frame(12))
        exporter = PdfExporter(repo)
        result = await exporter.render(PdfRequest(timeframe="30d"))
        assert result.content.startswith(PDF_MAGIC)

    @pytest.mark.asyncio
    async def test_filename_convention(self) -> None:
        repo = _FakePredictionRepo(btc=_btc_frame(12))
        exporter = PdfExporter(repo)
        result = await exporter.render(PdfRequest(timeframe="90d"))
        assert result.file_name.startswith("macro-crypto-report-90d-")
        assert result.file_name.endswith(".pdf")

    @pytest.mark.asyncio
    async def test_repo_receives_correct_hours(self) -> None:
        repo = _FakePredictionRepo(btc=_btc_frame(12))
        exporter = PdfExporter(repo)
        await exporter.render(PdfRequest(timeframe="30d"))
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
            exporter = PdfExporter(repo)
            await exporter.render(PdfRequest(timeframe=tf))
            assert repo.calls == [expected_hours], tf

    @pytest.mark.asyncio
    async def test_pdf_is_vector_not_raster(self) -> None:
        """A vector PDF for a single line plot is far smaller than
        the equivalent PNG at 300 DPI. This is the 'vector quality'
        check from the A2.4 acceptance criteria.
        """
        repo = _FakePredictionRepo(btc=_btc_frame(48))
        exporter = PdfExporter(repo)
        pdf_result = await exporter.render(PdfRequest(timeframe="30d"))

        # The PDF must be a small payload for a chart this size.
        # If it ever exceeds a few hundred KB, something is
        # rasterizing.
        assert pdf_result.file_size < 200_000, (
            f"PDF is {pdf_result.file_size} bytes — looks rasterized"
        )


# ============================================================
# render() — TITLE OVERRIDE
# ============================================================
class TestRenderTitle:
    """The title override is passed through to _render_pdf."""

    @pytest.mark.asyncio
    async def test_default_title_path(self) -> None:
        repo = _FakePredictionRepo(btc=_btc_frame(12))
        exporter = PdfExporter(repo)
        result = await exporter.render(
            PdfRequest(timeframe="30d", title=None)
        )
        assert result.rows_plotted == 12

    @pytest.mark.asyncio
    async def test_custom_title_path(self) -> None:
        repo = _FakePredictionRepo(btc=_btc_frame(12))
        exporter = PdfExporter(repo)
        result = await exporter.render(
            PdfRequest(timeframe="30d", title="Custom title")
        )
        assert result.rows_plotted == 12


# ============================================================
# RENDERER — FIGURE LIFECYCLE
# ============================================================
class TestRenderFigureLifecycle:
    """_render_pdf closes the figure it opens."""

    def test_figure_count_unchanged_after_render(self) -> None:
        import matplotlib.pyplot as plt

        before = len(plt.get_fignums())

        frame = _btc_frame(12)
        PdfExporter._render_pdf(
            frame=frame,
            timeframe="30d",
            title=None,
        )

        after = len(plt.get_fignums())
        assert after == before

    def test_render_does_not_raise_on_long_frame(self) -> None:
        frame = _btc_frame(500)
        payload = PdfExporter._render_pdf(
            frame=frame,
            timeframe="1y",
            title=None,
        )
        assert payload.startswith(PDF_MAGIC)