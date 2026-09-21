"""Export history repository.

Encapsulates all database reads and writes for the export_history
table (created in A2.1):
    - Writing new export requests (status='pending')
    - Updating rows as the export progresses (completed / failed)
    - Marking a row as downloaded
    - Reading history, filtered by user / status / timeframe

Design:
    - Takes an AsyncSession in the constructor. Callers wire the
      session from app.database.engine.session_scope().
    - Uses SQLAlchemy Core for queries (typesafe, parameterized).
    - Validates rows before insertion.
    - Does not commit — the caller controls the transaction.

Distinction from other repositories:
    - This repository is about *metadata* tracking (who requested
      what, when, and how it turned out). The file contents
      themselves are stored elsewhere (a filesystem or object
      store) and are not this repository's concern.
    - Unlike the other repositories in this package, this one
      performs UPDATE operations as the export lifecycle
      progresses (pending → completed/failed, downloaded_at set).
    - Rows are mutable: the export pipeline updates the same row
      multiple times rather than inserting a new row per state
      transition.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.tables import export_history

logger = logging.getLogger(__name__)


# ============================================================
# ROW DATACLASS
# ============================================================
@dataclass
class ExportHistoryRow:
    """A single row to insert into export_history.

    Represents a *new* export request. Fields that are populated
    later in the lifecycle (file_size, downloaded_at) are not part
    of this dataclass — they are set via the repository's update
    methods.

    Attributes:
        export_type: One of 'csv', 'png', 'pdf'.
        timeframe: One of '30d', '90d', '1y', '5y'.
        file_name: The generated filename.
        user_id: Optional opaque user identifier. None for
            system-triggered exports.
        data_types: JSON-serializable list of data-type strings
            (e.g. ['btc_price', 'correlations']).
        status: One of 'pending', 'completed', 'failed'. Defaults
            to 'pending' because a row is inserted when the request
            arrives, before the file is generated.
        file_size: Optional file size in bytes. Populated when the
            file is generated.
    """

    export_type: str
    timeframe: str
    file_name: str
    user_id: Optional[str] = None
    data_types: List[str] = field(default_factory=list)
    status: str = "pending"
    file_size: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dict suitable for SQLAlchemy insert()."""
        return {
            "user_id": self.user_id,
            "export_type": self.export_type,
            "data_types": list(self.data_types),
            "timeframe": self.timeframe,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "status": self.status,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ExportHistoryRow("
            f"export_type='{self.export_type}', "
            f"timeframe='{self.timeframe}', "
            f"file_name='{self.file_name}', "
            f"status='{self.status}', "
            f"user_id='{self.user_id}')"
        )


# ============================================================
# REPOSITORY
# ============================================================
class ExportHistoryRepository:
    """Repository for export_history reads and writes.

    All methods are async. The repository does not commit — the
    caller controls the transaction via session_scope().

    Example:
        async with session_scope() as session:
            repo = ExportHistoryRepository(session)
            export_id = await repo.create_request(row)
            await repo.mark_completed(
                export_id=export_id,
                file_name=row.file_name,
                file_size=1024,
            )
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: An AsyncSession bound to the target database.
        """
        self.session = session

    # ============================================================
    # WRITES — create
    # ============================================================
    async def create_request(self, row: ExportHistoryRow) -> int:
        """Insert a new export request and return its id.

        Validates the row before insertion. Does not commit — the
        caller controls the transaction via session_scope().

        Args:
            row: The export request to record.

        Returns:
            The generated `id` of the new row.

        Raises:
            ValueError: If the row fails validation.
        """
        # Validate before touching the database.
        from app.database.validators import validate_export_history_row

        payload = row.to_dict()
        validate_export_history_row(payload)

        # RETURNING gives us the id in one round-trip. Postgres
        # supports it; this repository is Postgres-only.
        stmt = (
            insert(export_history)
            .values(payload)
            .returning(export_history.c.id)
        )
        result = await self.session.execute(stmt)
        new_id = int(result.scalar_one())
        await self.session.flush()

        logger.info(
            f"Created export request id={new_id} "
            f"(type={row.export_type}, timeframe={row.timeframe}, "
            f"user={row.user_id})"
        )

        return new_id

    # ============================================================
    # WRITES — lifecycle updates
    # ============================================================
    async def mark_completed(
        self,
        export_id: int,
        file_name: str,
        file_size: int,
    ) -> int:
        """Mark an export as completed and record its file metadata.

        Does not commit — the caller controls the transaction.

        Args:
            export_id: The row id returned by create_request().
            file_name: The final filename.
            file_size: The file size in bytes.

        Returns:
            Number of rows updated (1 on success, 0 if the id does
            not exist).
        """
        stmt = (
            update(export_history)
            .where(export_history.c.id == export_id)
            .values(
                status="completed",
                file_name=file_name,
                file_size=file_size,
            )
        )
        result = await self.session.execute(stmt)
        await self.session.flush()

        rowcount = int(result.rowcount or 0)
        logger.info(
            f"Marked export id={export_id} completed "
            f"(file_name={file_name}, file_size={file_size})"
        )
        return rowcount

    async def mark_failed(self, export_id: int) -> int:
        """Mark an export as failed.

        The file_name column is NOT NULL at insert time, so the
        initial create_request call already supplied a provisional
        name. mark_failed leaves that name in place and only flips
        the status.

        Does not commit — the caller controls the transaction.

        Args:
            export_id: The row id.

        Returns:
            Number of rows updated (1 on success, 0 if the id does
            not exist).
        """
        stmt = (
            update(export_history)
            .where(export_history.c.id == export_id)
            .values(status="failed")
        )
        result = await self.session.execute(stmt)
        await self.session.flush()

        rowcount = int(result.rowcount or 0)
        logger.info(f"Marked export id={export_id} failed")
        return rowcount

    async def mark_downloaded(
        self,
        export_id: int,
        downloaded_at: Optional[datetime] = None,
    ) -> int:
        """Record that the file was downloaded.

        Does not commit — the caller controls the transaction.

        Args:
            export_id: The row id.
            downloaded_at: Timestamp to record. Defaults to now
                (UTC).

        Returns:
            Number of rows updated (1 on success, 0 if the id does
            not exist).
        """
        ts = downloaded_at or datetime.now(timezone.utc)
        stmt = (
            update(export_history)
            .where(export_history.c.id == export_id)
            .values(downloaded_at=ts)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()

        rowcount = int(result.rowcount or 0)
        logger.info(f"Marked export id={export_id} downloaded at {ts}")
        return rowcount

    # ============================================================
    # READS — single row
    # ============================================================
    async def fetch_by_id(
        self, export_id: int
    ) -> Optional[Dict[str, Any]]:
        """Fetch one export by id.

        Args:
            export_id: The row id.

        Returns:
            Dict with all columns, or None if no row exists.
        """
        stmt = select(
            export_history.c.id,
            export_history.c.user_id,
            export_history.c.export_type,
            export_history.c.data_types,
            export_history.c.timeframe,
            export_history.c.file_name,
            export_history.c.file_size,
            export_history.c.status,
            export_history.c.created_at,
            export_history.c.downloaded_at,
        ).where(export_history.c.id == export_id)

        result = await self.session.execute(stmt)
        row = result.mappings().first()

        return dict(row) if row else None

    # ============================================================
    # READS — history list
    # ============================================================
    async def fetch_history(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        timeframe: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Fetch recent export rows, filtered and ordered newest first.

        Args:
            user_id: Optional user filter.
            status: Optional status filter ('pending', 'completed',
                'failed').
            timeframe: Optional timeframe filter.
            limit: Maximum number of rows to return.

        Returns:
            List of dicts, ordered by created_at descending.
        """
        stmt = select(
            export_history.c.id,
            export_history.c.user_id,
            export_history.c.export_type,
            export_history.c.data_types,
            export_history.c.timeframe,
            export_history.c.file_name,
            export_history.c.file_size,
            export_history.c.status,
            export_history.c.created_at,
            export_history.c.downloaded_at,
        )

        if user_id is not None:
            stmt = stmt.where(export_history.c.user_id == user_id)
        if status is not None:
            stmt = stmt.where(export_history.c.status == status)
        if timeframe is not None:
            stmt = stmt.where(export_history.c.timeframe == timeframe)

        stmt = stmt.order_by(desc(export_history.c.created_at)).limit(limit)

        result = await self.session.execute(stmt)
        return [dict(row) for row in result.mappings().all()]

    # ============================================================
    # COUNTS
    # ============================================================
    async def count_rows(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """Return the total number of rows, optionally filtered.

        Useful for tests and monitoring.

        Args:
            user_id: Optional user filter.
            status: Optional status filter.

        Returns:
            Row count.
        """
        stmt = select(func.count()).select_from(export_history)

        if user_id is not None:
            stmt = stmt.where(export_history.c.user_id == user_id)
        if status is not None:
            stmt = stmt.where(export_history.c.status == status)

        result = await self.session.execute(stmt)
        return int(result.scalar_one())