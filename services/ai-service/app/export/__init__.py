"""AI Service — Export generation package.

This package owns the generation of analyst-facing export files
(CSV, PNG, PDF) from the same source data the API endpoints read.
The exports are byte-producing and side-effect-free at the
generation layer: the exporters themselves do not write files, do
not touch Redis, and do not call external services. Persisting the
bytes and recording the export in ``export_history`` is the
service layer's job (see ``app.export.service``).

A2.2 ships the CSV generator. A2.3 ships the PNG chart generator.
A2.4 ships the PDF chart generator. A2.5 adds a metadata and
citations block. A2.6 adds the storage layer that persists bytes
to disk and the download endpoint that serves them.

Available modules:
    - frames: shared per-data-type frame builders used by every
      exporter. All formats read the same source frames.
    - chart: shared chart construction and figure serialization,
      used by the PNG and PDF exporters.
    - metadata: metadata and citations block for exports.
    - csv_export: ``CsvExporter`` — builds a CSV byte payload from
      one or more requested data types over a chosen timeframe.
    - png_export: ``PngExporter`` — renders a single chart of BTC
      price over the chosen timeframe as a 300 DPI PNG.
    - pdf_export: ``PdfExporter`` — renders the same chart as a
      single-page vector PDF.
    - storage: ``ExportStorage`` protocol plus the local-disk and
      in-memory implementations (A2.6).
    - service: ``generate_csv_export``, ``generate_png_export``,
      and ``generate_pdf_export`` — session-owning wrappers that
      record the export in ``export_history``.
"""

from app.export.csv_export import (
    TIMEFRAME_DAYS,
    TIMEFRAME_HOURS,
    CsvExporter,
    ExportRequest,
    ExportResult,
)
from app.export.pdf_export import (
    PdfExporter,
    PdfRequest,
    PdfResult,
)
from app.export.png_export import (
    ChartRequest,
    ChartResult,
    PngExporter,
)
from app.export.storage import (
    ExportStorage,
    InMemoryStorage,
    LocalDiskStorage,
    get_storage,
)

__all__ = [
    # CSV exporter (A2.2)
    "CsvExporter",
    "ExportRequest",
    "ExportResult",
    "TIMEFRAME_HOURS",
    "TIMEFRAME_DAYS",
    # PNG exporter (A2.3)
    "PngExporter",
    "ChartRequest",
    "ChartResult",
    # PDF exporter (A2.4)
    "PdfExporter",
    "PdfRequest",
    "PdfResult",
    # Storage (A2.6)
    "ExportStorage",
    "InMemoryStorage",
    "LocalDiskStorage",
    "get_storage",
]