"""Export generation service.

Owns the session and the ``export_history`` write for a single CSV
export request. This is the wiring layer between the pure
``CsvExporter`` (which reads source tables and returns bytes) and
the ``ExportHistoryRepository`` (which records the request and its
outcome).

Design:

    - One public function, ``generate_csv_export``. It takes an
      ``ExportRequest``, opens one ``session_scope()``, and returns
      an ``ExportResult``. Callers do not see the session.
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
    - The exporter is constructed with the two repositories it
      needs, both bound to the same session, so the whole export is
      one transaction.

Usage:

    from app.export.csv_export import ExportRequest
    from app.export.service import generate_csv_export

    result = await generate_csv_export(
        ExportRequest(
            data_types=["btc_price", "correlations"],
            timeframe="90d",
            user_id="analyst-42",
        )
    )
    # result.content is the CSV bytes; result.file_name and
    # result.file_size match the row recorded in export_history.
"""

import logging
import time
from typing import Optional

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

logger = logging.getLogger(__name__)


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

        # ---- 1. Insert the pending row ----
        pending_row = ExportHistoryRow(
            export_type="csv",
            timeframe=request.timeframe,
            file_name=provisional_name,
            user_id=request.user_id,
            data_types=list(request.data_types),
            status="pending",
        )
        export_id = await history_repo.create_request(pending_row)

        logger.info(
            f"CSV export requested: id={export_id} "
            f"types={request.data_types} timeframe={request.timeframe} "
            f"user={request.user_id}"
        )

        # ---- 2. Build the CSV ----
        exporter = CsvExporter(
            prediction_repo=prediction_repo,
            correlation_repo=correlation_repo,
        )

        try:
            result = await exporter.build(request)
        except Exception as exc:
            # Transition the row to failed, then re-raise. The
            # session_scope rolls back on the propagating
            # exception, so this update is not persisted on this
            # branch — see module docstring. The mark_failed call
            # is kept so that A2.6 can flip a single flag to
            # persist failure rows once there is a persisted
            # artifact to reconcile against.
            try:
                await history_repo.mark_failed(export_id)
            except Exception as mark_exc:
                # Marking failed must never mask the original error.
                logger.warning(
                    f"Failed to mark export id={export_id} as failed: "
                    f"{mark_exc}"
                )

            logger.error(
                f"CSV export id={export_id} failed: {exc}",
                exc_info=True,
            )
            raise

        # ---- 3. Transition to completed ----
        await history_repo.mark_completed(
            export_id=export_id,
            file_name=result.file_name,
            file_size=result.file_size,
        )

        elapsed = time.monotonic() - start
        logger.info(
            f"CSV export id={export_id} completed: "
            f"file_name={result.file_name} "
            f"file_size={result.file_size} "
            f"rows={result.rows_written} "
            f"in {elapsed:.3f}s"
        )

        # ---- 4. Return ----
        return result


__all__ = ["generate_csv_export"]