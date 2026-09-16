"""Export generation service.

Owns the session, the ``export_history`` write, and the on-disk
persistence for every export request. This is the wiring layer
between the pure byte-producing exporters (``CsvExporter``,
``PngExporter``, ``PdfExporter``), the ``ExportHistoryRepository``
(which records the request and its outcome), and the
``ExportStorage`` backend (which persists the bytes).

Design:

    - One public function per export format:
      ``generate_csv_export``, ``generate_png_export``, and
      ``generate_pdf_export``. Each takes its format-specific
      request dataclass, opens one ``session_scope()``, and returns
      the format-specific result. Callers do not see the session
      or the storage backend.
    - The shared lifecycle (insert a ``pending`` row, run the
      exporter, persist the bytes, transition to ``completed`` or
      ``failed``) lives in ``_run_with_history``. The public
      functions are thin wrappers that wire up the right exporter
      and the right request shape.
    - The request is recorded with status='pending' before the
      exporter runs, then transitioned to 'completed' with the
      real file size reported by the storage layer. If the
      exporter or the storage save raises, the row is transitioned
      to 'failed' and the exception is re-raised.
    - Failure rows are not persisted on this branch. The
      ``session_scope()`` context manager rolls back the transaction
      when an exception propagates out of the block, which is the
      behaviour we want: a transient exporter or storage error
      should not leave a permanent 'failed' row behind. A2.6's
      download endpoint does not surface failed rows, so this
      remains correct.
    - ``mark_failed`` is best-effort. If it raises, the failure is
      logged and the original exporter/storage exception is
      re-raised unchanged — a cleanup error must never mask the
      real error.

Storage:

    - The storage backend is injected, not looked up inline. The
      public functions call ``get_storage()`` once and pass the
      result down to ``_run_with_history``. This keeps the
      singleton out of the shared helper's logic and lets tests
      monkeypatch ``get_storage`` on this module.
    - The bytes are persisted *before* the row transitions to
      ``completed``. If the save fails, the row is marked failed
      and the exception is re-raised, identical to an exporter
      failure. The bytes are not written partially — the
      ``LocalDiskStorage`` implementation writes to a temp file
      and renames atomically.
    - The ``file_size`` recorded on the completed row is the value
      returned by ``storage.save``, which reflects what the
      storage layer actually wrote. The result dataclass still
      carries the in-memory ``content`` for backward
      compatibility, but the download endpoint serves from
      storage, not from the result.

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
    # csv_result.file_name is the storage key.

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
    # the row recorded in export_history, and the bytes are
    # retrievable via the storage backend under result.file_name.
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
from app.export.storage import (
    ExportStorage,
    get_storage,
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
    storage: ExportStorage,
    export_type: str,
    timeframe: str,
    provisional_file_name: str,
    user_id: Optional[str],
    data_types: List[str],
    runner: Callable[[], Awaitable[T]],
    start_time: float,
) -> T:
    """Run an exporter, persist its bytes, record the outcome.

    Shared by ``generate_csv_export``, ``generate_png_export``, and
    ``generate_pdf_export``. The public functions differ only in the
    exporter they construct, the request shape they take, and the
    values they write into the history row. Everything else — the
    pending insert, the try/except around the exporter and the
    storage save, the completed transition, the mark_failed guard,
    the logging — is identical and lives here.

    Order of operations:

        1. Insert a ``pending`` row.
        2. Run the exporter to get the byte payload.
        3. Save the payload to storage.
        4. Transition the row to ``completed`` with the file size
           reported by storage.

    If step 2 or step 3 raises, the row is marked failed
    (best-effort) and the exception is re-raised unchanged.

    Args:
        history_repo: The export history repository, bound to the
            caller's session.
        storage: The storage backend to persist bytes into.
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
        Exception: Any exception raised by ``runner`` or by
            ``storage.save`` is logged, the history row is marked
            failed (best-effort), and the exception is re-raised
            unchanged.
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
        await _mark_failed_best_effort(history_repo, export_id)
        logger.error(
            f"{export_type.upper()} export id={export_id} "
            f"generation failed: {exc}",
            exc_info=True,
        )
        raise

    # ---- 3. Persist the bytes ----
    logger.debug(
        f"Persisting {len(result.content)} bytes at "
        f"{result.file_name!r} for export id={export_id}"
    )
    try:
        stored_size = storage.save(result.file_name, result.content)
    except Exception as exc:
        await _mark_failed_best_effort(history_repo, export_id)
        logger.error(
            f"{export_type.upper()} export id={export_id} "
            f"storage save failed for {result.file_name!r}: {exc}",
            exc_info=True,
        )
        raise

    # ---- 4. Transition to completed ----
    await history_repo.mark_completed(
        export_id=export_id,
        file_name=result.file_name,
        file_size=stored_size,
    )

    elapsed = time.monotonic() - start_time
    logger.info(
        f"{export_type.upper()} export id={export_id} completed: "
        f"file_name={result.file_name} "
        f"file_size={stored_size} "
        f"in {elapsed:.3f}s"
    )

    # ---- 5. Return ----
    return result


async def _mark_failed_best_effort(
    history_repo: ExportHistoryRepository,
    export_id: int,
) -> None:
    """Mark an export row failed, swallowing cleanup errors.

    Shared by both failure branches inside ``_run_with_history``.
    A cleanup error must never mask the original exception, so if
    ``mark_failed`` itself raises, the failure is logged and the
    caller is expected to re-raise the original exception.

    Args:
        history_repo: The export history repository.
        export_id: The row id.
    """
    try:
        await history_repo.mark_failed(export_id)
    except Exception as mark_exc:
        logger.warning(
            f"Failed to mark export id={export_id} as failed: "
            f"{mark_exc}"
        )


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
        3. Save the bytes to storage under the exporter's filename.
        4. Transition the row to ``completed`` with the real file
           size reported by storage.
        5. Return the ``ExportResult``.

    If step 2 or step 3 raises, the row is transitioned to
    ``failed`` and the exception is re-raised.

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
        Exception: Any other exception raised by ``build`` or by
            the storage save is logged and re-raised after marking
            the row failed.
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

    storage = get_storage()

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
            storage=storage,
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
    row, render the PNG, save the bytes to storage, transition to
    ``completed`` with the real file size. On failure, mark the row
    failed and re-raise.

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
        Exception: Any other exception raised by ``render`` or by
            the storage save is logged and re-raised after marking
            the row failed.
    """
    start = time.monotonic()

    # Provisional filename, computed up front so we can insert the
    # pending row before the exporter has produced anything.
    provisional_name = PngExporter._filename(request.timeframe)

    storage = get_storage()

    async with session_scope() as session:
        history_repo = ExportHistoryRepository(session)
        prediction_repo = PredictionRepository(session)

        exporter = PngExporter(prediction_repo=prediction_repo)

        return await _run_with_history(
            history_repo=history_repo,
            storage=storage,
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
    vector PDF, save the bytes to storage, transition to
    ``completed`` with the real file size. On failure, mark the row
    failed and re-raise.

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
        Exception: Any other exception raised by ``render`` or by
            the storage save is logged and re-raised after marking
            the row failed.
    """
    start = time.monotonic()

    # Provisional filename, computed up front so we can insert the
    # pending row before the exporter has produced anything.
    provisional_name = PdfExporter._filename(request.timeframe)

    storage = get_storage()

    async with session_scope() as session:
        history_repo = ExportHistoryRepository(session)
        prediction_repo = PredictionRepository(session)

        exporter = PdfExporter(prediction_repo=prediction_repo)

        return await _run_with_history(
            history_repo=history_repo,
            storage=storage,
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