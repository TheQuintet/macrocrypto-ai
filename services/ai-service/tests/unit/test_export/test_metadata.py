"""Unit tests for app.export.metadata.

Covers:
    - DataSource dataclass: citation rendering with and without a
      URL, to_dict, __repr__
    - MethodologyReference dataclass: citation rendering with and
      without a URL, to_dict, __repr__
    - ExportMetadata dataclass: to_citation_lines,
      to_footer_text, to_comment_lines, to_dict, __repr__,
      significance_note handling
    - Canonical constants: FRED_SOURCE, COINGECKO_SOURCE,
      AI_SERVICE_SOURCE, METHODOLOGY
    - SOURCE_FOR_DATA_TYPE mapping
    - build_metadata: default sources, filtered sources,
      deduplication, ordering, significance_note pass-through,
      accessed_at default vs. explicit

Pure-function tests — no I/O, no mocks. Every test that needs a
deterministic timestamp passes an explicit ``accessed_at``.
"""

from datetime import datetime, timezone
from typing import List

import pytest

from app.export.metadata import (
    AI_SERVICE_SOURCE,
    COINGECKO_SOURCE,
    FRED_SOURCE,
    METHODOLOGY,
    SOURCE_FOR_DATA_TYPE,
    DataSource,
    ExportMetadata,
    MethodologyReference,
    build_metadata,
)


# ============================================================
# FIXTURES
# ============================================================
FIXED_TS = datetime(2026, 9, 16, 14, 32, 0, tzinfo=timezone.utc)


# ============================================================
# DataSource
# ============================================================
class TestDataSource:
    """DataSource.citation and serialization."""

    def test_citation_with_url(self) -> None:
        src = DataSource(name="FRED", url="https://fred.example", description="")
        assert src.citation() == "FRED (https://fred.example)"

    def test_citation_without_url(self) -> None:
        src = DataSource(name="Internal", url="", description="")
        assert src.citation() == "Internal"

    def test_to_dict_round_trip(self) -> None:
        src = DataSource(
            name="X", url="https://x.example", description="desc"
        )
        assert src.to_dict() == {
            "name": "X",
            "url": "https://x.example",
            "description": "desc",
        }

    def test_repr_contains_key_fields(self) -> None:
        src = DataSource(
            name="Y", url="https://y.example", description=""
        )
        text = repr(src)
        assert "Y" in text
        assert "https://y.example" in text

    def test_frozen(self) -> None:
        """DataSource is frozen; mutation raises."""
        src = DataSource(name="Z", url="", description="")
        with pytest.raises(Exception):
            src.name = "other"  # type: ignore[misc]


# ============================================================
# MethodologyReference
# ============================================================
class TestMethodologyReference:
    """MethodologyReference.citation and serialization."""

    def test_citation_without_url(self) -> None:
        m = MethodologyReference(name="Method", version="1.0.0", url="")
        assert m.citation() == "Method v1.0.0"

    def test_citation_with_url(self) -> None:
        m = MethodologyReference(
            name="Method", version="2.3.1", url="https://m.example"
        )
        assert m.citation() == "Method v2.3.1 (https://m.example)"

    def test_to_dict_round_trip(self) -> None:
        m = MethodologyReference(
            name="X", version="1.0.0", url="", description="desc"
        )
        assert m.to_dict() == {
            "name": "X",
            "version": "1.0.0",
            "url": "",
            "description": "desc",
        }

    def test_repr_contains_key_fields(self) -> None:
        m = MethodologyReference(name="M", version="9.9", url="")
        text = repr(m)
        assert "M" in text
        assert "9.9" in text

    def test_frozen(self) -> None:
        m = MethodologyReference(name="M", version="1.0", url="")
        with pytest.raises(Exception):
            m.version = "2.0"  # type: ignore[misc]


# ============================================================
# ExportMetadata — rendering
# ============================================================
class TestExportMetadataRendering:
    """to_citation_lines, to_footer_text, to_comment_lines."""

    def _make(self, **overrides) -> ExportMetadata:
        defaults = dict(
            sources=[FRED_SOURCE, COINGECKO_SOURCE],
            methodology=METHODOLOGY,
            accessed_at=FIXED_TS,
            significance_note=None,
        )
        defaults.update(overrides)
        return ExportMetadata(**defaults)

    def test_citation_lines_without_significance(self) -> None:
        md = self._make()
        lines = md.to_citation_lines()
        assert len(lines) == 3
        assert lines[0].startswith("Sources: FRED (https://fred.stlouisfed.org)")
        assert "CoinGecko (https://www.coingecko.com)" in lines[0]
        assert lines[1] == "Methodology: MacroCrypto AI methodology v1.0.0"
        assert lines[2] == "Accessed: 2026-09-16 14:32 UTC"

    def test_citation_lines_with_significance(self) -> None:
        md = self._make(significance_note="p<0.05")
        lines = md.to_citation_lines()
        assert len(lines) == 4
        assert lines[2] == "Significance: p<0.05"
        assert lines[3].startswith("Accessed: ")

    def test_citation_lines_with_empty_sources(self) -> None:
        md = self._make(sources=[])
        lines = md.to_citation_lines()
        # "Sources: " with an empty tail, then Methodology, then
        # Accessed.
        assert lines[0] == "Sources: "

    def test_footer_text_is_newline_joined(self) -> None:
        md = self._make(significance_note="note")
        text = md.to_footer_text()
        assert text == "\n".join(md.to_citation_lines())
        assert text.count("\n") == 3  # 4 lines → 3 newlines

    def test_footer_text_without_significance(self) -> None:
        md = self._make()
        text = md.to_footer_text()
        assert text.count("\n") == 2  # 3 lines → 2 newlines

    def test_comment_lines_default_prefix(self) -> None:
        md = self._make()
        for line in md.to_comment_lines():
            assert line.startswith("# ")

    def test_comment_lines_custom_prefix(self) -> None:
        md = self._make()
        for line in md.to_comment_lines(prefix="// "):
            assert line.startswith("// ")

    def test_comment_lines_match_citation_lines(self) -> None:
        md = self._make(significance_note="note")
        stripped = [line[len("# "):] for line in md.to_comment_lines()]
        assert stripped == md.to_citation_lines()


# ============================================================
# ExportMetadata — serialization
# ============================================================
class TestExportMetadataSerialization:
    """ExportMetadata.to_dict and __repr__."""

    def test_to_dict_shape(self) -> None:
        md = ExportMetadata(
            sources=[FRED_SOURCE],
            methodology=METHODOLOGY,
            accessed_at=FIXED_TS,
            significance_note=None,
        )
        d = md.to_dict()
        assert d["sources"] == [FRED_SOURCE.to_dict()]
        assert d["methodology"] == METHODOLOGY.to_dict()
        assert d["accessed_at"] == FIXED_TS.isoformat()
        assert d["significance_note"] is None

    def test_to_dict_with_significance(self) -> None:
        md = ExportMetadata(
            sources=[],
            methodology=METHODOLOGY,
            accessed_at=FIXED_TS,
            significance_note="p<0.05",
        )
        assert md.to_dict()["significance_note"] == "p<0.05"

    def test_to_dict_is_json_serializable(self) -> None:
        import json

        md = ExportMetadata(
            sources=[FRED_SOURCE, COINGECKO_SOURCE],
            methodology=METHODOLOGY,
            accessed_at=FIXED_TS,
            significance_note=None,
        )
        # Should not raise.
        json.dumps(md.to_dict())

    def test_repr_contains_source_names_and_version(self) -> None:
        md = ExportMetadata(
            sources=[FRED_SOURCE, COINGECKO_SOURCE],
            methodology=METHODOLOGY,
            accessed_at=FIXED_TS,
        )
        text = repr(md)
        assert "FRED" in text
        assert "CoinGecko" in text
        assert "1.0.0" in text


# ============================================================
# Canonical constants
# ============================================================
class TestCanonicalConstants:
    """The shipped constants are stable and self-consistent."""

    def test_fred_source(self) -> None:
        assert FRED_SOURCE.name == "FRED"
        assert FRED_SOURCE.url.startswith("https://")
        assert "fred" in FRED_SOURCE.url.lower()

    def test_coingecko_source(self) -> None:
        assert COINGECKO_SOURCE.name == "CoinGecko"
        assert COINGECKO_SOURCE.url.startswith("https://")
        assert "coingecko" in COINGECKO_SOURCE.url.lower()

    def test_ai_service_source_has_no_url(self) -> None:
        """The AI Service is an internal source; no public URL."""
        assert AI_SERVICE_SOURCE.name == "MacroCrypto AI Service"
        assert AI_SERVICE_SOURCE.url == ""

    def test_methodology_version_is_semver_like(self) -> None:
        parts = METHODOLOGY.version.split(".")
        assert len(parts) == 3
        for p in parts:
            int(p)  # must be an integer

    def test_methodology_name_and_description(self) -> None:
        assert METHODOLOGY.name
        assert METHODOLOGY.description

    def test_source_for_data_type_covers_all_exporters(self) -> None:
        # Every data type the CSV exporter produces, plus the
        # chart type the PNG/PDF exporters produce.
        expected = {
            "btc_price",
            "macro",
            "predictions",
            "correlations",
            "regimes",
            "chart",
        }
        assert expected.issubset(SOURCE_FOR_DATA_TYPE.keys())

    def test_btc_price_maps_to_coingecko(self) -> None:
        names = [s.name for s in SOURCE_FOR_DATA_TYPE["btc_price"]]
        assert names == ["CoinGecko"]

    def test_macro_maps_to_fred(self) -> None:
        names = [s.name for s in SOURCE_FOR_DATA_TYPE["macro"]]
        assert names == ["FRED"]

    def test_chart_maps_to_coingecko_and_ai_service(self) -> None:
        names = [s.name for s in SOURCE_FOR_DATA_TYPE["chart"]]
        assert names == ["CoinGecko", "MacroCrypto AI Service"]

    def test_prediction_and_correlation_map_to_three_sources(self) -> None:
        for dt in ("predictions", "correlations"):
            names = [s.name for s in SOURCE_FOR_DATA_TYPE[dt]]
            assert names == [
                "CoinGecko",
                "FRED",
                "MacroCrypto AI Service",
            ]


# ============================================================
# build_metadata
# ============================================================
class TestBuildMetadata:
    """build_metadata source resolution and pass-through."""

    def test_default_includes_all_three_sources(self) -> None:
        md = build_metadata(accessed_at=FIXED_TS)
        names = [s.name for s in md.sources]
        assert names == ["FRED", "CoinGecko", "MacroCrypto AI Service"]

    def test_single_data_type_filter(self) -> None:
        md = build_metadata(
            data_types=["btc_price"], accessed_at=FIXED_TS
        )
        names = [s.name for s in md.sources]
        assert names == ["CoinGecko"]

    def test_multi_data_type_deduplicates_and_preserves_order(self) -> None:
        md = build_metadata(
            data_types=["btc_price", "macro", "chart"],
            accessed_at=FIXED_TS,
        )
        # btc_price → CoinGecko; macro → FRED; chart → CoinGecko
        # (dup) + AI Service. Result order should be first-seen.
        names = [s.name for s in md.sources]
        assert names == ["CoinGecko", "FRED", "MacroCrypto AI Service"]

    def test_unknown_data_type_is_silently_ignored(self) -> None:
        """An unknown data type contributes no sources."""
        md = build_metadata(
            data_types=["bogus"], accessed_at=FIXED_TS
        )
        assert md.sources == []

    def test_empty_data_types_list(self) -> None:
        md = build_metadata(data_types=[], accessed_at=FIXED_TS)
        assert md.sources == []

    def test_significance_note_pass_through(self) -> None:
        md = build_metadata(
            data_types=["correlations"],
            significance_note="Pearson p-values; alpha=0.05",
            accessed_at=FIXED_TS,
        )
        assert md.significance_note == "Pearson p-values; alpha=0.05"

    def test_significance_note_defaults_to_none(self) -> None:
        md = build_metadata(accessed_at=FIXED_TS)
        assert md.significance_note is None

    def test_accessed_at_explicit(self) -> None:
        md = build_metadata(accessed_at=FIXED_TS)
        assert md.accessed_at == FIXED_TS

    def test_accessed_at_defaults_to_now_utc(self) -> None:
        before = datetime.now(timezone.utc)
        md = build_metadata()
        after = datetime.now(timezone.utc)
        assert before <= md.accessed_at <= after
        assert md.accessed_at.tzinfo is not None

    def test_methodology_is_always_the_canonical_one(self) -> None:
        md = build_metadata(accessed_at=FIXED_TS)
        assert md.methodology is METHODOLOGY

    def test_frozen_result(self) -> None:
        md = build_metadata(accessed_at=FIXED_TS)
        with pytest.raises(Exception):
            md.significance_note = "x"  # type: ignore[misc]