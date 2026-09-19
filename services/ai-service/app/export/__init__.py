"""AI Service — Export generation package.

This package owns the generation of analyst-facing export files
(CSV, PNG, PDF) from the same source data the API endpoints read.
The exports are byte-producing and side-effect-free: they do not
write files to disk, do not touch Redis, and do not call external
services. Persisting the bytes (local disk or object store) and
recording the export in ``export_history`` is the caller's job —
see ``app.export.service``.

A2.2 ships the CSV generator. PNG and PDF land in A2.3 and A2.4.

Available modules:
    - csv_export: ``CsvExporter`` — builds a CSV byte payload from
      one or more requested data types over a chosen timeframe.
"""

from app.export.csv_export import (
    TIMEFRAME_DAYS,
    TIMEFRAME_HOURS,
    CsvExporter,
    ExportRequest,
    ExportResult,
)

__all__ = [
    "CsvExporter",
    "ExportRequest",
    "ExportResult",
    "TIMEFRAME_HOURS",
    "TIMEFRAME_DAYS",
]