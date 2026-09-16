"""Export generation service.

Owns the session and the ``export_history`` write for every export
request. This is the wiring layer between the pure byte-producing
exporters (``CsvExporter``, ``PngExporter``, ``PdfExporter``) and
the ``ExportHistoryRepository`` (which records the request and its
outcome).

Design:

    - One public function per export format:
      ``generate_csv_export``, ``generate_png_export``, and
      ``generate_pdf_export``. Each takes its format-specific
      request dataclass, opens one ``session_scope()``, and returns
      the format-specific result. Callers do not see the session.
    - The shared lifecycle (insert a ``pending`` row, run the
      exporter, transition to ``completed`` or ``failed``) lives in
      ``_run_with_history``. The public functions are thin
      wrappers that wire up the right exporter and the right
      request shape.
    - The request is recorded with status='pending' before the
      exporter runs, then transitioned to 'completed' with the real
      file size. If the exporter raises, the row is transitioned to
      'failed' and the exception is re-raised.
    - Failure rows are not persisted on this branch. The
      ``session_scope()`` context manager rolls back the transaction
      when an exception propagates out of the block, which is the
      behaviour we want: a transient exporter error should not
      leave a permanent 'failed' row behind. A2.6 (file storage)
      will revisit this when there is a persisted artifact to
      reconcile against.
    - ``mark_failed`` is best-effort. If it raises, the failure is
      logged and the original exporter exception is re-raised
      unchanged — a cleanup error must never mask the real error.

Usage:

    from app.export.csv_export import ExportRequest
    from app.export.png_export import ChartRequest
    from app.export.pdf_export import PdfRequest
    from app.export.service import (
        generate_csv_export,
        generate_png_export,
        generate_pdf_export,
    )

    # CSV
    csv_result = await generate_csv_export(
        ExportRequest(
            data_types=["btc_price", "correlations"],
            timeframe="90d",
            user_id="analyst-42",
        )
    )
    # csv_result.content is the CSV bytes.

    # PNG
    png_result = await generate_png_export(
        ChartRequest(timeframe="90d", user_id="analyst-42")
    )
    # png_result.content is the PNG bytes.

    # PDF
    pdf_result = await generate_pdf_export(
        PdfRequest(timeframe="90d", user_id="analyst-42")
    )
    # pdf_result.content is the PDF bytes.

    # In every case, result.file_name and result.file_size match
    # the row recorded in export_history.
"""

import logging
import time
from typing import Any, Awaitable, Callable, List, Optional, TypeVar

from app.database.engine import session_scope
from app.database.repositories.correlation_repository import (
    CorrelationRepository,
)
from app.database.repositories.export_history_repository import (
    ExportHistoryRepository,
    ExportHistoryRow,
)
from app.database.repositories.prediction_repository import (
    PredictionRepository,
)
from app.export.csv_export import (
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

logger = logging.getLogger(__name__)


# The result type is ExportResult (CSV), ChartResult (PNG), or
# PdfResult (PDF). All three carry file_name, file_size, and
# content, which is all the shared lifecycle needs.
T = TypeVar("T")


# ============================================================
# SHARED LIFECYCLE
# ============================================================
async def _run_with_history(
    *,
    history_repo: ExportHistoryRepository,
    export_type: str,
    timeframe: str,
    provisional_file_name: str,
    user_id: Optional[str],
    data_types: List[str],
    runner: Callable[[], Awaitable[T]],
    start_time: float,
) -> T:
    """Run an exporter and record the request in ``export_history``.

    Shared by ``generate_csv_export``, ``generate_png_export``, and
    ``generate_pdf_export``. The public functions differ only in the
    exporter they construct, the request shape they take, and the
    values they write into the history row. Everything else — the
    pending insert, the try/except around the exporter, the
    completed transition, the mark_failed guard, the logging — is
    identical and lives here.

    Args:
        history_repo: The export history repository, bound to the
            caller's session.
        export_type: One of 'csv', 'png', 'pdf'.
        timeframe: One of '30d', '90d', '1y', '5y'.
        provisional_file_name: Filename to write into the pending
            row. The column is NOT NULL; the completed transition
            overwrites this with the exporter's final filename.
        user_id: Optional opaque identifier. ``None`` for
            system-triggered exports.
        data_types: Data types to record on the history row. For
            CSV this is the requested stream list; for PNG and PDF
            this is the single-element list ``['chart']``.
        runner: Zero-argument callable that builds the export and
            returns the format-specific result. Called exactly once.
        start_time: ``time.monotonic()`` value captured by the
            caller before opening the session, used for the elapsed
            log line.

    Returns:
        Whatever ``runner`` returns.

    Raises:
        Exception: Any exception raised by ``runner`` is logged,
            the history row is marked failed (best-effort), and the
            exception is re-raised unchanged.
    """
    # ---- 1. Insert the pending row ----
    pending_row = ExportHistoryRow(
        export_type=export_type,
        timeframe=timeframe,
        file_name=provisional_file_name,
        user_id=user_id,
        data_types=list(data_types),
        status="pending",
    )
    export_id = await history_repo.create_request(pending_row)

    logger.info(
        f"{export_type.upper()} export requested: id={export_id} "
        f"types={data_types} timeframe={timeframe} "
        f"user={user_id}"
    )

    # ---- 2. Run the exporter ----
    try:
        result = await runner()
    except Exception as exc:
        # Transition the row to failed, then re-raise. The
        # session_scope rolls back on the propagating exception,
        # so this update is not persisted on this branch — see
        # module docstring. The mark_failed call is kept so that
        # A2.6 can flip a single flag to persist failure rows once
        # there is a persisted artifact to reconcile against.
        try:
            await history_repo.mark_failed(export_id)
        except Exception as mark_exc:
            # Marking failed must never mask the original error.
            logger.warning(
                f"Failed to mark export id={export_id} as failed: "
                f"{mark_exc}"
            )

        logger.error(
            f"{export_type.upper()} export id={export_id} failed: "
            f"{exc}",
            exc_info=True,
        )
        raise

    # ---- 3. Transition to completed ----
    await history_repo.mark_completed(
        export_id=export_id,
        file_name=result.file_name,
        file_size=result.file_size,
    )

    elapsed = time.monotonic() - start_time
    logger.info(
        f"{export_type.upper()} export id={export_id} completed: "
        f"file_name={result.file_name} "
        f"file_size={result.file_size} "
        f"in {elapsed:.3f}s"
    )

    # ---- 4. Return ----
    return result


# ============================================================
# CSV EXPORT
# ============================================================
async def generate_csv_export(
    request: ExportRequest,
) -> ExportResult:
    """Generate a CSV export and record it in ``export_history``.

    Steps, all inside one ``session_scope()``:

        1. Insert a ``pending`` row into ``export_history`` with a
           provisional filename derived from the request.
        2. Build the CSV bytes via ``CsvExporter.build``.
        3. Transition the row to ``completed`` with the real file
           size and filename.
        4. Return the ``ExportResult``.

    If step 2 raises, the row is transitioned to ``failed`` and the
    exception is re-raised. Because the session_scope rolls back on
    a propagating exception, the failed-request row is NOT persisted
    on this branch — see the module docstring for why.

    Args:
        request: The export request. ``request.data_types`` and
            ``request.timeframe`` drive the export; ``request.user_id``
            is recorded on the history row if set.

    Returns:
        The ``ExportResult`` produced by the exporter, including the
        CSV bytes.

    Raises:
        ValueError: Propagated from ``CsvExporter.build`` for an
            unknown timeframe, empty or unsupported data types, or
            an empty result frame.
        Exception: Any other exception raised by ``build`` is
            logged and re-raised after marking the row failed.
    """
    start = time.monotonic()

    # Provisional filename, computed up front so we can insert the
    # pending row before the exporter has produced anything. The
    # final filename from ``build()`` is expected to match unless
    # the caller has a single data type and a future exporter
    # chooses a different segment; in that case the completed row
    # overwrites this value.
    provisional_name = CsvExporter._filename(
        data_types=list(request.data_types),
        timeframe=request.timeframe,
    )

    async with session_scope() as session:
        history_repo = ExportHistoryRepository(session)
        prediction_repo = PredictionRepository(session)
        correlation_repo = CorrelationRepository(session)

        exporter = CsvExporter(
            prediction_repo=prediction_repo,
            correlation_repo=correlation_repo,
        )

        return await _run_with_history(
            history_repo=history_repo,
            export_type="csv",
            timeframe=request.timeframe,
            provisional_file_name=provisional_name,
            user_id=request.user_id,
            data_types=list(request.data_types),
            runner=lambda: exporter.build(request),
            start_time=start,
        )


# ============================================================
# PNG EXPORT
# ============================================================
async def generate_png_export(
    request: ChartRequest,
) -> ChartResult:
    """Generate a PNG chart export and record it in ``export_history``.

    Same lifecycle as ``generate_csv_export``: insert a ``pending``
    row, render the PNG, transition to ``completed`` with the real
    file size. On failure, mark the row failed and re-raise.

    The history row is recorded with ``export_type='png'`` and
    ``data_types=['chart']``. ``'chart'`` is a storage-level label
    added to ``VALID_DATA_TYPE_NAMES`` for A2.3; it does not
    correspond to a data stream a CSV exporter produces.

    Args:
        request: The chart request. ``request.timeframe`` drives the
            chart; ``request.user_id`` is recorded on the history
            row if set; ``request.title`` overrides the default
            chart title.

    Returns:
        The ``ChartResult`` produced by the exporter, including the
        PNG bytes.

    Raises:
        ValueError: Propagated from ``PngExporter.render`` for an
            unknown timeframe or an empty BTC price frame.
        Exception: Any other exception raised by ``render`` is
            logged and re-raised after marking the row failed.
    """
    start = time.monotonic()

    # Provisional filename, computed up front so we can insert the
    # pending row before the exporter has produced anything.
    provisional_name = PngExporter._filename(request.timeframe)

    async with session_scope() as session:
        history_repo = ExportHistoryRepository(session)
        prediction_repo = PredictionRepository(session)

        exporter = PngExporter(prediction_repo=prediction_repo)

        return await _run_with_history(
            history_repo=history_repo,
            export_type="png",
            timeframe=request.timeframe,
            provisional_file_name=provisional_name,
            user_id=request.user_id,
            data_types=["chart"],
            runner=lambda: exporter.render(request),
            start_time=start,
        )


# ============================================================
# PDF EXPORT
# ============================================================
async def generate_pdf_export(
    request: PdfRequest,
) -> PdfResult:
    """Generate a PDF chart export and record it in ``export_history``.

    Same lifecycle as ``generate_csv_export`` and
    ``generate_png_export``: insert a ``pending`` row, render the
    vector PDF, transition to ``completed`` with the real file size.
    On failure, mark the row failed and re-raise.

    The history row is recorded with ``export_type='pdf'`` and
    ``data_types=['chart']``. The ``'chart'`` label is the same
    storage-level marker the PNG path uses; the ``export_type``
    column is what distinguishes PDF from PNG.

    Args:
        request: The PDF request. ``request.timeframe`` drives the
            chart; ``request.user_id`` is recorded on the history
            row if set; ``request.title`` overrides the default
            chart title.

    Returns:
        The ``PdfResult`` produced by the exporter, including the
        PDF bytes.

    Raises:
        ValueError: Propagated from ``PdfExporter.render`` for an
            unknown timeframe or an empty BTC price frame.
        Exception: Any other exception raised by ``render`` is
            logged and re-raised after marking the row failed.
    """
    start = time.monotonic()

    # Provisional filename, computed up front so we can insert the
    # pending row before the exporter has produced anything.
    provisional_name = PdfExporter._filename(request.timeframe)

    async with session_scope() as session:
        history_repo = ExportHistoryRepository(session)
        prediction_repo = PredictionRepository(session)

        exporter = PdfExporter(prediction_repo=prediction_repo)

        return await _run_with_history(
            history_repo=history_repo,
            export_type="pdf",
            timeframe=request.timeframe,
            provisional_file_name=provisional_name,
            user_id=request.user_id,
            data_types=["chart"],
            runner=lambda: exporter.render(request),
            start_time=start,
        )


__all__ = [
    "generate_csv_export",
    "generate_png_export",
    "generate_pdf_export",
]