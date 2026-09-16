"""Metadata and citation block for analyst exports (A2.5).

Every analyst-facing export — CSV, PNG, PDF — carries a citations
block naming the data sources, the methodology reference, and the
access timestamp. This module is that block.

The block is a static structure of *references* (source names,
source URLs, methodology name and version) plus one computed field:
the access timestamp, which is ``now()`` at render time. The
references are not deployment-varying configuration — FRED's URL is
FRED's URL in dev and in prod — so they live here rather than in
``app.config``. That also keeps the block a pure-function test
target with no monkeypatching.

Citations-ready output:

    Sources: FRED (https://fred.stlouisfed.org), CoinGecko (https://www.coingecko.com)
    Methodology: MacroCrypto AI methodology v1.0.0
    Accessed: 2026-09-16 14:32 UTC

The same three lines are rendered into:

    - the footer of the chart Figure (PNG and PDF), via
      ``app.export.chart.build_chart_figure``.
    - the comment header of a CSV export, via
      ``app.export.csv_export.CsvExporter.to_csv``.

``SOURCE_FOR_DATA_TYPE`` maps each data-type name the exporters
produce to the sources that contributed to it. It is what the
service and exporter layers consult when they need to know which
citations apply to a given export.

Design:

    - Pure construction. ``build_metadata`` reads no external state
      and touches no I/O. It is safe to call from anywhere.
    - Dataclasses are frozen, so an ``ExportMetadata`` instance can
      be shared across call sites without risk of mutation.
    - ``to_dict`` is JSON-serialisable. This is what lands in
      ``ExportResult.to_dict`` / ``ChartResult.to_dict`` /
      ``PdfResult.to_dict`` so downstream consumers can inspect the
      citations programmatically.
"""

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================
# DATACLASSES
# ============================================================
@dataclass(frozen=True)
class DataSource:
    """A single data source cited in an export.

    Attributes:
        name: Human-readable source name (e.g. "FRED").
        url: Base URL of the source (e.g. "https://fred.stlouisfed.org").
            May be empty for sources without a public URL (e.g. the
            AI Service's own derived tables).
        description: One-sentence description of what the source
            contributes.
    """

    name: str
    url: str
    description: str

    def citation(self) -> str:
        """Return a single-line citation string.

        ``"FRED (https://fred.stlouisfed.org)"`` when a URL is set;
        ``"MacroCrypto AI Service"`` when it is not.
        """
        if self.url:
            return f"{self.name} ({self.url})"
        return self.name

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable dict."""
        return asdict(self)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"DataSource(name={self.name!r}, url={self.url!r})"


@dataclass(frozen=True)
class MethodologyReference:
    """A reference to the methodology used to produce an export.

    Attributes:
        name: Human-readable methodology name.
        version: Version string. Bumped when the methodology
            changes in a way that would change the numbers.
        url: Optional URL to fuller documentation. Empty if the
            methodology lives only in the codebase.
        description: One-sentence summary of the method.
    """

    name: str
    version: str
    url: str = ""
    description: str = ""

    def citation(self) -> str:
        """Return a single-line citation string.

        ``"<name> v<version>"``, optionally with a URL.
        """
        base = f"{self.name} v{self.version}"
        if self.url:
            return f"{base} ({self.url})"
        return base

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable dict."""
        return asdict(self)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"MethodologyReference(name={self.name!r}, "
            f"version={self.version!r})"
        )


@dataclass(frozen=True)
class ExportMetadata:
    """The full citations block attached to an export.

    Attributes:
        sources: The data sources that contributed to this export.
        methodology: The methodology reference.
        accessed_at: When the export was rendered (UTC). Computed
            at build time, not configured.
        significance_note: Optional statistical-significance note.
            Populated when the export includes derived metrics
            (correlations, predictions) whose confidence intervals
            or p-values are relevant. ``None`` for exports that
            contain only raw observations.
    """

    sources: List[DataSource]
    methodology: MethodologyReference
    accessed_at: datetime
    significance_note: Optional[str] = None

    # --- rendering ---------------------------------------------------

    def to_citation_lines(self) -> List[str]:
        """Return the citations block as a list of plain text lines.

        Three or four lines, in this order:

            Sources: <source 1>, <source 2>, ...
            Methodology: <methodology citation>
            Significance: <significance note>   (only if set)
            Accessed: <YYYY-MM-DD HH:MM UTC>
        """
        lines = [
            "Sources: " + ", ".join(s.citation() for s in self.sources),
            f"Methodology: {self.methodology.citation()}",
        ]
        if self.significance_note:
            lines.append(f"Significance: {self.significance_note}")
        lines.append(
            "Accessed: "
            + self.accessed_at.astimezone(timezone.utc).strftime(
                "%Y-%m-%d %H:%M UTC"
            )
        )
        return lines

    def to_footer_text(self) -> str:
        """Return the citations block as one newline-joined string.

        This is what ``chart.build_chart_figure`` writes into the
        figure footer. It is the multi-line form of
        :meth:`to_citation_lines`.
        """
        return "\n".join(self.to_citation_lines())

    def to_comment_lines(self, prefix: str = "# ") -> List[str]:
        """Return the citations block as prefixed comment lines.

        This is what ``CsvExporter.to_csv`` prepends to the CSV
        payload. Lines start with ``prefix`` (default ``"# "``) so
        that ``pandas.read_csv(..., comment="#")`` ignores them on
        re-import.
        """
        return [prefix + line for line in self.to_citation_lines()]

    # --- serialization -----------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable dict.

        The ``accessed_at`` field is rendered as an ISO 8601 string.
        """
        return {
            "sources": [s.to_dict() for s in self.sources],
            "methodology": self.methodology.to_dict(),
            "accessed_at": self.accessed_at.isoformat(),
            "significance_note": self.significance_note,
        }

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"ExportMetadata("
            f"sources={[s.name for s in self.sources]}, "
            f"methodology={self.methodology.name!r} "
            f"v{self.methodology.version})"
        )


# ============================================================
# CANONICAL SOURCES
# ============================================================
FRED_SOURCE = DataSource(
    name="FRED",
    url="https://fred.stlouisfed.org",
    description=(
        "Federal Reserve Economic Data — CPI, interest rate, "
        "M2 growth, DXY, treasury yield."
    ),
)

COINGECKO_SOURCE = DataSource(
    name="CoinGecko",
    url="https://www.coingecko.com",
    description=(
        "BTC price, volume, market dominance, active addresses."
    ),
)

AI_SERVICE_SOURCE = DataSource(
    name="MacroCrypto AI Service",
    url="",
    description=(
        "Derived outputs: predictions, correlations, regime labels."
    ),
)


# ============================================================
# CANONICAL METHODOLOGY
# ============================================================
METHODOLOGY = MethodologyReference(
    name="MacroCrypto AI methodology",
    version="1.0.0",
    url="",
    description=(
        "Pearson correlation over 30/90/365-day windows; "
        "walk-forward backtests; regime classification via "
        "app.prediction.market.classify_market_condition_safe."
    ),
)


# ============================================================
# SOURCE MAPPING
# ============================================================
# Which sources contributed to each data type the exporters can
# produce. The order within each list is the order the citations
# are rendered in.
SOURCE_FOR_DATA_TYPE: Dict[str, List[DataSource]] = {
    "btc_price": [COINGECKO_SOURCE],
    "macro": [FRED_SOURCE],
    "predictions": [COINGECKO_SOURCE, FRED_SOURCE, AI_SERVICE_SOURCE],
    "correlations": [COINGECKO_SOURCE, FRED_SOURCE, AI_SERVICE_SOURCE],
    "regimes": [COINGECKO_SOURCE, AI_SERVICE_SOURCE],
    # The chart exporters (PNG, PDF) plot BTC price plus the
    # methodology-derived trend, so their source list includes the
    # BTC source and the methodology is captured separately.
    "chart": [COINGECKO_SOURCE, AI_SERVICE_SOURCE],
}


# ============================================================
# BUILDERS
# ============================================================
def build_metadata(
    *,
    data_types: Optional[List[str]] = None,
    significance_note: Optional[str] = None,
    accessed_at: Optional[datetime] = None,
) -> ExportMetadata:
    """Build an ``ExportMetadata`` for one export.

    Args:
        data_types: The data-type names the export covers. When
            provided, the resulting source list is the union of
            ``SOURCE_FOR_DATA_TYPE[dt]`` for each name, deduplicated
            while preserving first-seen order. When ``None``, all
            canonical sources are included.
        significance_note: Optional statistical-significance
            sentence. ``None`` for exports that contain only raw
            observations.
        accessed_at: Timestamp to record. Defaults to
            ``datetime.now(timezone.utc)``. Pass an explicit value
            in tests for determinism.

    Returns:
        A frozen :class:`ExportMetadata` instance.
    """
    if accessed_at is None:
        accessed_at = datetime.now(timezone.utc)

    if data_types is None:
        # No data-type filter → include every canonical source.
        sources: List[DataSource] = [
            FRED_SOURCE,
            COINGECKO_SOURCE,
            AI_SERVICE_SOURCE,
        ]
    else:
        seen_names: set = set()
        sources = []
        for dt in data_types:
            for src in SOURCE_FOR_DATA_TYPE.get(dt, []):
                if src.name in seen_names:
                    continue
                seen_names.add(src.name)
                sources.append(src)

    return ExportMetadata(
        sources=sources,
        methodology=METHODOLOGY,
        accessed_at=accessed_at,
        significance_note=significance_note,
    )


__all__ = [
    "AI_SERVICE_SOURCE",
    "COINGECKO_SOURCE",
    "DataSource",
    "ExportMetadata",
    "FRED_SOURCE",
    "METHODOLOGY",
    "MethodologyReference",
    "SOURCE_FOR_DATA_TYPE",
    "build_metadata",
]