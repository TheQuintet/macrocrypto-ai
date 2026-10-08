"""
Tests for the Phase B migration runner (app/database/migrate.py).

These tests exercise the runner's *bookkeeping* logic:
  - apply migrations in lexical order
  - record applied versions in schema_migrations
  - skip already-applied files
  - be idempotent on re-run
  - roll back a failing file without recording it

They deliberately do NOT exercise the real migration files in
services/data-service/migrations/. Those are Postgres-only
(TIMESTAMPTZ, SERIAL, create_hypertable) and cannot run against
SQLite. The real files are covered by integration testing against
a live Postgres database; this module isolates the runner logic so
it can be tested deterministically and in CI without a database
container.

If a Postgres test fixture is introduced later, these tests can be
parametrized on the engine without changing their assertions.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.database import migrate as migrate_module


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture
def fake_migrations_dir(tmp_path, monkeypatch):
    """
    A temp migrations directory with three trivial, valid SQL files.

    The runner is pointed at this directory via monkeypatch so the
    real migrations/ directory is never read by these tests.
    """
    (tmp_path / "001_a.sql").write_text(
        "CREATE TABLE a (id INTEGER PRIMARY KEY);"
    )
    (tmp_path / "002_b.sql").write_text(
        "CREATE TABLE b (id INTEGER PRIMARY KEY);"
    )
    (tmp_path / "003_add_schema_migrations.sql").write_text(
        "CREATE TABLE c (id INTEGER PRIMARY KEY);"
    )

    monkeypatch.setattr(
        migrate_module,
        "MIGRATIONS_DIR",
        tmp_path,
    )
    return tmp_path


@pytest.fixture
def sqlite_engine(tmp_path):
    """
    A fresh SQLite database, discarded after the test.

    SQLite is sufficient for the runner's bookkeeping logic. It is
    not sufficient for the real Postgres-only migration files.
    """
    db_path = tmp_path / "test_migrate.db"
    engine = create_engine(f"sqlite:///{db_path}")
    try:
        yield engine
    finally:
        engine.dispose()


def _recorded_versions(engine) -> list[str]:
    """Helper: return applied versions in order, or [] if no table."""
    with engine.connect() as conn:
        try:
            rows = conn.execute(
                text(
                    "SELECT version FROM schema_migrations "
                    "ORDER BY version"
                )
            ).all()
        except (OperationalError, ProgrammingError):
            return []
    return [row[0] for row in rows]


def _table_exists(engine, name: str) -> bool:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name=:name"
            ),
            {"name": name},
        ).fetchone()
    return row is not None


# ============================================================
# TESTS
# ============================================================


def test_run_migrations_applies_all_in_order(
    fake_migrations_dir,
    sqlite_engine,
):
    """
    On a fresh database, every file is applied in lexical order and
    every version is recorded in schema_migrations.
    """
    applied = migrate_module.run_migrations(bind=sqlite_engine)

    assert applied == [
        "001_a.sql",
        "002_b.sql",
        "003_add_schema_migrations.sql",
    ]

    assert _recorded_versions(sqlite_engine) == [
        "001_a.sql",
        "002_b.sql",
        "003_add_schema_migrations.sql",
    ]

    # The DDL from each file actually ran.
    assert _table_exists(sqlite_engine, "a")
    assert _table_exists(sqlite_engine, "b")
    assert _table_exists(sqlite_engine, "c")


def test_run_migrations_is_idempotent(
    fake_migrations_dir,
    sqlite_engine,
):
    """
    Running twice does not re-apply anything the second time.
    """
    first = migrate_module.run_migrations(bind=sqlite_engine)
    second = migrate_module.run_migrations(bind=sqlite_engine)

    assert first == [
        "001_a.sql",
        "002_b.sql",
        "003_add_schema_migrations.sql",
    ]
    assert second == []

    # Row count in schema_migrations is unchanged after the second
    # call (no duplicate INSERTs).
    assert _recorded_versions(sqlite_engine) == [
        "001_a.sql",
        "002_b.sql",
        "003_add_schema_migrations.sql",
    ]


def test_run_migrations_skips_already_applied(
    fake_migrations_dir,
    sqlite_engine,
):
    """
    A version already present in schema_migrations is not re-applied,
    even if the file is still on disk.
    """
    # Hand-seed schema_migrations with 001 as if a previous run had
    # applied it. The 'a' table must already exist, otherwise the
    # runner will try to apply 001 and fail on CREATE TABLE a.
    with sqlite_engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE schema_migrations (
                    version     TEXT        PRIMARY KEY,
                    applied_at  TIMESTAMP   NOT NULL
                                DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                "INSERT INTO schema_migrations (version) "
                "VALUES ('001_a.sql')"
            )
        )
        conn.execute(text("CREATE TABLE a (id INTEGER PRIMARY KEY)"))

    applied = migrate_module.run_migrations(bind=sqlite_engine)

    assert applied == [
        "002_b.sql",
        "003_add_schema_migrations.sql",
    ]
    assert _recorded_versions(sqlite_engine) == [
        "001_a.sql",
        "002_b.sql",
        "003_add_schema_migrations.sql",
    ]


def test_run_migrations_rolls_back_failed_file(
    tmp_path,
    sqlite_engine,
    monkeypatch,
):
    """
    A file that fails mid-apply is not recorded, and its partial DDL
    is rolled back. Previously applied files remain applied.
    """
    (tmp_path / "001_ok.sql").write_text(
        "CREATE TABLE ok (id INTEGER PRIMARY KEY);"
    )
    (tmp_path / "002_bad.sql").write_text(
        "CREATE TABLE bad (this is not valid SQL);"
    )
    monkeypatch.setattr(
        migrate_module,
        "MIGRATIONS_DIR",
        tmp_path,
    )

    with pytest.raises(Exception):
        migrate_module.run_migrations(bind=sqlite_engine)

    # 001 is applied and recorded; 002 is not recorded.
    assert _recorded_versions(sqlite_engine) == ["001_ok.sql"]

    # 001's table exists; 002's table does not (it never created).
    assert _table_exists(sqlite_engine, "ok")
    assert not _table_exists(sqlite_engine, "bad")


def test_run_migrations_handles_empty_directory(
    tmp_path,
    sqlite_engine,
    monkeypatch,
):
    """
    An empty migrations directory is not an error; the runner
    creates schema_migrations and returns [].
    """
    monkeypatch.setattr(
        migrate_module,
        "MIGRATIONS_DIR",
        tmp_path,
    )

    applied = migrate_module.run_migrations(bind=sqlite_engine)

    assert applied == []
    # schema_migrations still exists after the run.
    assert _table_exists(sqlite_engine, "schema_migrations")