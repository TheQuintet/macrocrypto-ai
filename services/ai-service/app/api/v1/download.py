"""Export download endpoint.

Serves the byte payloads persisted by ``app.export.service`` via
``app.export.storage``. The endpoint is a thin read path:

    - It looks up the ``export_history`` row by ``file_name``
      (the storage key). A missing row, or a row whose status is
      not ``completed``, is a 404: the file is either not yet
      written or was never written.
    - It loads the bytes from storage. A missing file is a 404,
      which is the case when the cleanup job has already removed
      an expired export.
    - It records the download on the row via
      ``ExportHistoryRepository.mark_downloaded``. That call is
      best-effort: if it fails, the download still succeeds, but
      the failure is logged.
    - It returns the bytes.

Response shape:

    - When the storage backend is ``LocalDiskStorage``, the
      response is a ``FileResponse`` streaming from disk. FastAPI
      sets ``Content-Length`` and ``Content-Disposition`` from
      the filename, and supports range requests.
    - For any other backend (``InMemoryStorage`` in tests, a
      future S3 backend), the bytes are loaded into memory and
      returned as a ``Response``. Same headers, different
      mechanism.

Design notes:

    - The endpoint does NOT enforce the link TTL. Expiry is the
      cleanup job's responsibility (files past TTL are deleted;
      a load on a deleted file raises ``FileNotFoundError``,
      which this handler turns into 404). Keeping the endpoint
      read-only means a file that has not yet been swept is still
      downloadable; that matches the ticket's intent ("download
      links expire after configured time") without forcing the
      endpoint to also be a garbage collector.
    - The endpoint does NOT check ownership. The A2.6 ticket does
      not include authentication, and the row's ``user_id`` is an
      opaque identifier not tied to any identity system yet. A
      later branch that adds auth will layer an ownership check
      here. For now the endpoint is open, matching the existing
      predict/performance/correlation routers.
    - A 404 for "row missing", "row not completed", and "file
      missing" is deliberate. Distinguishing them would leak
      information (which exports exist but are not yet ready)
      without helping any caller.

Usage:

    GET /api/v1/exports/macro-crypto-btc_price-30d-2026-09-16.csv
    -> 200 with the CSV bytes, or 404 if the export is not ready
       or has expired.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, Response

from app.database.engine import session_scope
from app.database.repositories.export_history_repository import (
    ExportHistoryRepository,
)
from app.export.storage import (
    ExportStorage,
    LocalDiskStorage,
    get_storage,
)

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/v1/exports",
    tags=["exports"],
)


# ============================================================
# CONTENT TYPES
# ============================================================
# Map the ``export_type`` value recorded on the history row to a
# MIME type for the response. Kept here rather than in a schema
# module because it is only used by this handler.
_CONTENT_TYPES: Dict[str, str] = {
    "csv": "text/csv",
    "png": "image/png",
    "pdf": "application/pdf",
}


# ============================================================
# HELPERS
# ============================================================
async def _lookup_ready_export(
    history_repo: ExportHistoryRepository,
    file_name: str,
) -> Dict[str, Any]:
    """Return the export_history row for ``file_name`` if it is ready.

    A row is "ready" when it exists and its status is ``completed``.
    Rows in any other state (``pending``, ``failed``, or missing)
    raise a 404.

    Args:
        history_repo: The export history repository.
        file_name: The storage key / filename to look up.

    Returns:
        The row as a dict.

    Raises:
        HTTPException: 404 if the row is missing or not completed.
    """
    # ``fetch_by_id`` is keyed on the primary key, not on
    # ``file_name``. This branch does not add a new repository
    # method; instead, the handler queries via ``fetch_history``
    # filtered by the exact file name. There is at most one row
    # per file name in practice (the exporter's filename includes
    # a date and a data-type, and re-running the same export on
    # the same day reuses the same name). If that ever becomes a
    # concern, add a ``fetch_by_file_name`` method to the
    # repository and switch to it.
    candidates = await history_repo.fetch_history(limit=1000)
    match: Optional[Dict[str, Any]] = next(
        (r for r in candidates if r["file_name"] == file_name),
        None,
    )

    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No export found for {file_name!r}",
        )

    if match["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Export {file_name!r} is not ready "
                f"(status={match['status']!r})"
            ),
        )

    return match


def _build_response(
    storage: ExportStorage,
    key: str,
    export_type: str,
) -> Response:
    """Return the appropriate FastAPI response for ``key``.

    Uses ``FileResponse`` for local-disk storage (streams from
    disk, supports range requests, sets the filename header) and
    a plain ``Response`` for any other backend (loads the bytes
    into memory).

    Args:
        storage: The storage backend.
        key: The storage key (filename).
        export_type: One of 'csv', 'png', 'pdf'.

    Returns:
        A FastAPI response object.
    """
    media_type = _CONTENT_TYPES.get(
        export_type, "application/octet-stream"
    )

    if isinstance(storage, LocalDiskStorage):
        # Streaming response from disk. FastAPI sets
        # Content-Length, Content-Disposition, and handles range
        # requests automatically.
        return FileResponse(
            path=storage.path_for(key),
            media_type=media_type,
            filename=key,
        )

    # Non-filesystem backend: load into memory.
    try:
        content = storage.load(key)
    except FileNotFoundError:
        # The row says completed but the file is gone. This can
        # happen when the cleanup job has swept an expired file
        # before the corresponding row was deleted (rows are not
        # deleted on this branch — only files are).
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export file {key!r} is no longer available",
        )

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{key}"',
        },
    )


# ============================================================
# ENDPOINTS
# ============================================================
@router.get(
    "/{file_name}",
    summary="Download a generated export",
    response_class=FileResponse,
    responses={
        200: {
            "description": "The export bytes",
            "content": {
                "text/csv": {},
                "image/png": {},
                "application/pdf": {},
            },
        },
        404: {
            "description": (
                "No export exists for the given filename, the "
                "export is not yet completed, or the file has "
                "expired and been cleaned up."
            ),
        },
    },
)
async def download_export(file_name: str) -> Response:
    """Download a generated export by filename.

    Args:
        file_name: The storage key (filename) of the export.
            Usually generated by one of the export service
            functions and surfaced in a prior API response.

    Returns:
        The export bytes as a stream (local disk) or an in-memory
        response (other backends).

    Raises:
        HTTPException: 404 if the export row is missing or not
            completed, or if the file has been removed from
            storage.
    """
    storage = get_storage()

    async with session_scope() as session:
        history_repo = ExportHistoryRepository(session)

        # ---- 1. Look up the row and confirm it is ready ----
        row = await _lookup_ready_export(history_repo, file_name)
        export_id = int(row["id"])
        export_type = row["export_type"]

        # ---- 2. Confirm the file exists in storage ----
        # For LocalDiskStorage this is a cheap stat. For other
        # backends, ``exists`` is also cheap (dict lookup).
        if not storage.exists(file_name):
            logger.warning(
                f"Export id={export_id} marked completed but file "
                f"{file_name!r} is missing from storage"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Export file {file_name!r} is no longer available",
            )

        # ---- 3. Record the download (best-effort) ----
        try:
            await history_repo.mark_downloaded(export_id)
            # The repository does not commit — session_scope
            # commits on successful exit. The commit covers both
            # the mark_downloaded update and any other writes in
            # this block (none today).
        except Exception as exc:
            # Never fail the download because the audit trail
            # write failed.
            logger.warning(
                f"Failed to record download for export id={export_id}: "
                f"{exc}"
            )

        # ---- 4. Build and return the response ----
        # The response object is constructed while the session is
        # still open (so ``path_for`` has a valid backend), but
        # the bytes themselves are streamed by FastAPI after this
        # coroutine returns. That is fine for local disk: the
        # file lives on disk independent of the session.
        return _build_response(storage, file_name, export_type)


__all__ = ["router"]