"""Simple SQL migration runner for the AI Service.

Reads `.sql` files from the `migrations/` directory and applies them
in lexicographic order, tracking applied migrations in a
`schema_migrations` table.

Design:
    - No new dependencies (uses the existing async SQLAlchemy engine)
    - Idempotent: already-applied migrations are skipped
    - Each migration runs inside its own transaction
    - Logs each step for visibility
    - Runnable as `python -m app.database.migrations_runner`

Safety:
    - The runner reads the migrations directory path from settings
      so it can be relocated without code changes.
    - It does NOT wrap everything in a single transaction — that
      would make partial failures unrecoverable. Instead, each
      migration commits on success and records itself atomically.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.engine import dispose_engine, get_engine

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
# The `schema_migrations` table is created by migration 001.
# If the table doesn't exist yet, we can't query it — so we
# special-case the first run.
SCHEMA_MIGRATIONS_TABLE = "schema_migrations"


# ============================================================
# MIGRATION FILE DISCOVERY
# ============================================================
def discover_migrations(migrations_dir: Path) -> List[Path]:
    """Return the sorted list of `.sql` files in a directory.

    Args:
        migrations_dir: Directory containing `.sql` migration files.

    Returns:
        List of Path objects, sorted lexicographically by filename.
        Returns an empty list if the directory doesn't exist or
        contains no `.sql` files.
    """
    if not migrations_dir.exists() or not migrations_dir.is_dir():
        logger.warning(
            f"Migrations directory does not exist: {migrations_dir}"
        )
        return []

    files = sorted(migrations_dir.glob("*.sql"))

    logger.debug(
        f"Discovered {len(files)} migration file(s) in {migrations_dir}"
    )

    return files


# ============================================================
# MIGRATION STATE
# ============================================================
async def _schema_migrations_table_exists(
    session: AsyncSession,
) -> bool:
    """Return True if the schema_migrations table already exists.

    Uses a Postgres-specific information_schema query.

    Args:
        session: An AsyncSession bound to the target database.

    Returns:
        True if the table exists, False otherwise.
    """
    result = await session.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_name = :table_name
            )
            """
        ),
        {"table_name": SCHEMA_MIGRATIONS_TABLE},
    )
    return bool(result.scalar())


async def _get_applied_versions(session: AsyncSession) -> List[str]:
    """Return the list of already-applied migration versions.

    If the schema_migrations table doesn't exist yet, returns an
    empty list (nothing has been applied).

    Args:
        session: An AsyncSession bound to the target database.

    Returns:
        List of migration version strings (filenames).
    """
    if not await _schema_migrations_table_exists(session):
        return []

    result = await session.execute(
        text(
            f"SELECT version FROM {SCHEMA_MIGRATIONS_TABLE} "
            f"ORDER BY version ASC"
        )
    )
    return [row[0] for row in result.all()]


async def _record_migration(
    session: AsyncSession,
    version: str,
) -> None:
    """Record a successfully applied migration in schema_migrations.

    Args:
        session: An AsyncSession bound to the target database.
        version: The migration version (filename) to record.
    """
    await session.execute(
        text(
            f"INSERT INTO {SCHEMA_MIGRATIONS_TABLE} (version) "
            f"VALUES (:version)"
        ),
        {"version": version},
    )


# ============================================================
# MIGRATION APPLICATION
# ============================================================
async def _apply_migration(
    session: AsyncSession,
    migration_path: Path,
) -> None:
    """Apply a single migration file inside the given session.

    The caller is responsible for committing / rolling back.

    Args:
        session: An AsyncSession bound to the target database.
        migration_path: Path to the `.sql` file to apply.

    Raises:
        RuntimeError: If the SQL fails to execute.
    """
    version = migration_path.name
    sql = migration_path.read_text(encoding="utf-8")

    if not sql.strip():
        logger.warning(f"Migration file is empty: {version}")
        return

    logger.info(f"Applying migration: {version}")

    # Execute the raw SQL. SQLAlchemy's text() wrapper handles
    # multiple statements when the driver supports it (asyncpg does
    # for DDL when using the exec_driver_sql path, but here we use
    # execute with a single script — asyncpg will split it).
    try:
        # `exec_driver_sql` allows multi-statement scripts and
        # bypasses SQLAlchemy's parameter binding (which would
        # choke on `::type` casts and dollar-quoted strings).
        raw = await session.connection()
        await raw.exec_driver_sql(sql)
    except Exception as e:
        raise RuntimeError(
            f"Migration '{version}' failed: {e}"
        ) from e

    # Record the migration as applied
    await _record_migration(session, version)

    logger.info(f"Applied migration: {version}")


async def run_migrations(
    migrations_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> Tuple[int, int]:
    """Run all pending migrations.

    Args:
        migrations_dir: Override the default migrations directory.
            If None, uses the configured path.
        dry_run: If True, discover and log pending migrations but
            do not apply them.

    Returns:
        A tuple `(applied_count, skipped_count)`.
    """
    if migrations_dir is None:
        migrations_dir = _default_migrations_dir()

    logger.info(f"Running migrations from: {migrations_dir}")

    # ---- 1. Discover migration files ----
    files = discover_migrations(migrations_dir)

    if not files:
        logger.info("No migrations found — nothing to do")
        return (0, 0)

    # ---- 2. Open a session and read applied versions ----
    engine = get_engine()

    async with engine.begin() as conn:
        # Temporary session wrapper for the pre-checks
        from sqlalchemy.ext.asyncio import AsyncSession as _AS

        session = _AS(bind=conn)  # type: ignore[arg-type]

        try:
            applied = set(await _get_applied_versions(session))
        finally:
            pass  # `engine.begin()` handles commit/rollback

    logger.info(
        f"Found {len(files)} migration file(s), "
        f"{len(applied)} already applied"
    )

    # ---- 3. Apply pending migrations ----
    pending = [f for f in files if f.name not in applied]

    if not pending:
        logger.info("All migrations are up to date")
        return (0, len(files))

    logger.info(
        f"Applying {len(pending)} pending migration(s): "
        f"{[f.name for f in pending]}"
    )

    if dry_run:
        logger.info("Dry-run mode: not applying migrations")
        return (0, len(files))

    applied_count = 0
    for migration in pending:
        async with engine.begin() as conn:
            from sqlalchemy.ext.asyncio import AsyncSession as _AS

            session = _AS(bind=conn)  # type: ignore[arg-type]
            await _apply_migration(session, migration)
        applied_count += 1

    return (applied_count, len(files) - applied_count)


def _default_migrations_dir() -> Path:
    """Return the default migrations directory.

    Assumes the standard layout:
        services/ai-service/migrations/

    `app/database/migrations_runner.py` → up 3 levels → service root.

    Returns:
        Path to the migrations directory.
    """
    current = Path(__file__).resolve()
    # current: .../services/ai-service/app/database/migrations_runner.py
    service_root = current.parent.parent.parent
    return service_root / "migrations"


# ============================================================
# ENTRY POINT
# ============================================================
async def async_main(argv: Optional[List[str]] = None) -> int:
    """Async entry point.

    Args:
        argv: Optional argument list (unused for now; reserved for
            future --dry-run / --dir flags).

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        applied, skipped = await run_migrations()
        logger.info(
            f"Migrations complete: {applied} applied, "
            f"{skipped} already up to date"
        )
        return 0
    except Exception as e:
        logger.error(f"Migration run failed: {e}", exc_info=True)
        return 1
    finally:
        await dispose_engine()


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point.

    Args:
        argv: Optional argument list (uses sys.argv if None).

    Returns:
        Exit code.
    """
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        force=True,
    )
    return asyncio.run(async_main(argv))


if __name__ == "__main__":
    sys.exit(main())