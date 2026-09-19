"""AI Service — Export generation package.

This package owns the generation of analyst-facing export files
(CSV, PNG, PDF) from the same source data the API endpoints read.
The exports are byte-producing and side-effect-free: they do not
write files to disk, do not touch Redis, and do not call external
services. Persisting the bytes (local disk or object store) and
recording the export in ``export_history`` is the caller's job —
see ``app.export.service``.

A2.2 ships the CSV generator. A2.3 ships the PNG chart generator.
PDF lands in A2.4.

Available modules:
    - frames: shared per-data-type frame builders used by both
      exporters. Both formats read the same source frames.
    - csv_export: ``CsvExporter`` — builds a CSV byte payload from
      one or more requested data types over a chosen timeframe.
    - png_export: ``PngExporter`` — renders a single chart of BTC
      price over the chosen timeframe as a 300 DPI PNG.
    - service: ``generate_csv_export`` and ``generate_png_export`` —
      session-owning wrappers that record the export in
      ``export_history``.
"""

from app.export.csv_export import (
    TIMEFRAME_DAYS,
    TIMEFRAME_HOURS,
    CsvExporter,
    ExportRequest,
    ExportResult,
)
from app.export.png_export import (
    ChartRequest,
    ChartResult,
    PngExporter,
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
]