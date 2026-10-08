"""
Migration runner for the data-service.

Reads migrations/*.sql in lexical order, tracks applied versions in
the schema_migrations table, and applies unapplied migrations one
transaction at a time.

- One transaction per file: a failure rolls back only that file.
- The schema_migrations INSERT is inside the same transaction as
  the DDL, so partial application is impossible.
- Idempotent: re-running with everything applied is a no-op.

Usage:
    python -m app.database.migrate       # CLI
    from app.database.migrate import run_migrations
    run_migrations()                      # programmatic
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine


logger = logging.getLogger(__name__)


# services/data-service/migrations/
MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def _ensure_schema_migrations_table(conn) -> None:
    """Mirror 003; called before scanning so recording 003 works."""
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version     TEXT        PRIMARY KEY,
                applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
    )


def _applied_versions(conn) -> set[str]:
    rows = conn.execute(
        text("SELECT version FROM schema_migrations")
    ).all()
    return {row[0] for row in rows}


def _migration_files() -> list[Path]:
    if not MIGRATIONS_DIR.is_dir():
        raise RuntimeError(
            f"Migrations directory not found: {MIGRATIONS_DIR}"
        )
    return sorted(
        p for p in MIGRATIONS_DIR.iterdir()
        if p.is_file() and p.suffix == ".sql"
    )


def run_migrations(bind: Engine | None = None) -> list[str]:
    """
    Apply all unapplied migrations.

    Args:
        bind: optional Engine; defaults to the shared engine in
              app.database.session. Tests pass their own.

    Returns:
        The list of migration filenames applied during this call.
        Empty if the database was already up to date.
    """
    if bind is None:
        from app.database.session import engine as bind

    applied_now: list[str] = []

    # 1. Ensure tracking table exists (its own transaction).
    with bind.begin() as conn:
        _ensure_schema_migrations_table(conn)

    # 2. Read what's already applied.
    with bind.connect() as conn:
        already = _applied_versions(conn)

    files = _migration_files()
    logger.info(
        "Migration runner: %d file(s) on disk, %d already applied",
        len(files),
        len(already),
    )

    # 3. Apply unapplied files in lexical order, one tx each.
    for path in files:
        version = path.name
        if version in already:
            logger.debug("Skipping already-applied %s", version)
            continue

        sql = path.read_text(encoding="utf-8")
        logger.info("Applying migration %s", version)

        with bind.begin() as conn:
            conn.execute(text(sql))
            conn.execute(
                text(
                    "INSERT INTO schema_migrations (version) "
                    "VALUES (:version)"
                ),
                {"version": version},
            )

        applied_now.append(version)
        logger.info("Applied migration %s", version)

    if applied_now:
        logger.info(
            "Migration runner: applied %d migration(s): %s",
            len(applied_now),
            ", ".join(applied_now),
        )
    else:
        logger.info("Migration runner: database is up to date")

    return applied_now


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        applied = run_migrations()
    except Exception:
        logger.exception("Migration runner failed")
        return 1
    if not applied:
        print("Database is up to date; nothing to apply.")
    else:
        print(f"Applied {len(applied)} migration(s):")
        for v in applied:
            print(f"  - {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())