"""Schema-level tests for the export_history table (A2.1).

These tests verify the *shape* of the Core Table and the migration
file — column names, types, nullability, defaults, indexes, and the
CHECK constraints / comments in the SQL. They do not touch a live
database; they inspect the SQLAlchemy metadata and read the
migration file as text.
"""

import re
from pathlib import Path

import pytest
from sqlalchemy import BigInteger, DateTime, String

from app.database.tables import (
    TABLE_EXPORT_HISTORY,
    export_history,
    metadata,
)


# ============================================================
# CONSTANTS
# ============================================================
MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "migrations"
MIGRATION_FILE = MIGRATIONS_DIR / "009_create_export_history.sql"

EXPECTED_COLUMNS = [
    "id",
    "user_id",
    "export_type",
    "data_types",
    "timeframe",
    "file_name",
    "file_size",
    "status",
    "created_at",
    "downloaded_at",
]

# Columns that must carry a COMMENT ON COLUMN in the migration.
# `id` is deliberately excluded: a BIGINT PRIMARY KEY is
# self-documenting, and migration 009 does not comment it.
EXPECTED_COMMENTED_COLUMNS = [
    "user_id",
    "export_type",
    "data_types",
    "timeframe",
    "file_name",
    "file_size",
    "status",
    "created_at",
    "downloaded_at",
]

EXPECTED_INDEXES = {
    "idx_export_history_user_id",
    "idx_export_history_created_at",
    "idx_export_history_user_created",
}


# ============================================================
# MODULE-LEVEL FIXTURE
# ============================================================
@pytest.fixture(scope="module")
def sql() -> str:
    """Read the migration file once per module and share it.

    Defined at module scope (not on the test class) so pytest's
    fixture discovery can see it. A class-scoped fixture defined as
    an instance method is deprecated in pytest 9 and removed in
    pytest 10; defining it at module scope avoids both the
    deprecation and the classmethod-registration problem.
    """
    assert MIGRATION_FILE.exists(), (
        f"Migration file not found: {MIGRATION_FILE}"
    )
    return MIGRATION_FILE.read_text(encoding="utf-8")


# ============================================================
# CORE TABLE
# ============================================================
class TestExportHistoryTable:
    """Shape of the Core Table object in app.database.tables."""

    def test_constant_name(self):
        assert TABLE_EXPORT_HISTORY == "export_history"

    def test_table_name(self):
        assert export_history.name == "export_history"

    def test_registered_in_metadata(self):
        assert "export_history" in metadata.tables
        assert metadata.tables["export_history"] is export_history

    def test_column_names_and_order(self):
        assert [c.name for c in export_history.columns] == EXPECTED_COLUMNS

    def test_id_is_bigint_primary_key(self):
        col = export_history.c.id
        assert isinstance(col.type, BigInteger)
        assert col.primary_key is True
        assert col.nullable is False

    def test_user_id_is_nullable_varchar_64(self):
        col = export_history.c.user_id
        assert isinstance(col.type, String)
        assert col.type.length == 64
        assert col.nullable is True

    def test_export_type_is_not_null_varchar_8(self):
        col = export_history.c.export_type
        assert isinstance(col.type, String)
        assert col.type.length == 8
        assert col.nullable is False

    def test_data_types_is_not_null_jsonb(self):
        col = export_history.c.data_types
        # JSONB comes from sqlalchemy.dialects.postgresql; import
        # lazily to avoid a hard dependency at module import time.
        from sqlalchemy.dialects.postgresql import JSONB

        assert isinstance(col.type, JSONB)
        assert col.nullable is False

    def test_timeframe_is_not_null_varchar_8(self):
        col = export_history.c.timeframe
        assert isinstance(col.type, String)
        assert col.type.length == 8
        assert col.nullable is False

    def test_file_name_is_not_null_varchar_255(self):
        col = export_history.c.file_name
        assert isinstance(col.type, String)
        assert col.type.length == 255
        assert col.nullable is False

    def test_file_size_is_nullable_bigint(self):
        col = export_history.c.file_size
        assert isinstance(col.type, BigInteger)
        assert col.nullable is True

    def test_status_is_not_null_varchar_16(self):
        col = export_history.c.status
        assert isinstance(col.type, String)
        assert col.type.length == 16
        assert col.nullable is False

    def test_created_at_is_not_null_timestamptz(self):
        col = export_history.c.created_at
        assert isinstance(col.type, DateTime)
        assert col.type.timezone is True
        assert col.nullable is False

    def test_downloaded_at_is_nullable_timestamptz(self):
        col = export_history.c.downloaded_at
        assert isinstance(col.type, DateTime)
        assert col.type.timezone is True
        assert col.nullable is True

    def test_indexes_present(self):
        names = {idx.name for idx in export_history.indexes}
        assert EXPECTED_INDEXES.issubset(names)

    def test_user_id_index(self):
        idx = next(
            i for i in export_history.indexes
            if i.name == "idx_export_history_user_id"
        )
        assert [c.name for c in idx.columns] == ["user_id"]

    def test_created_at_index(self):
        idx = next(
            i for i in export_history.indexes
            if i.name == "idx_export_history_created_at"
        )
        assert [c.name for c in idx.columns] == ["created_at"]

    def test_user_created_composite_index(self):
        idx = next(
            i for i in export_history.indexes
            if i.name == "idx_export_history_user_created"
        )
        assert [c.name for c in idx.columns] == ["user_id", "created_at"]


# ============================================================
# MIGRATION FILE
# ============================================================
class TestExportHistoryMigration:
    """Content of migrations/009_create_export_history.sql."""

    def test_file_exists(self):
        assert MIGRATION_FILE.exists()
        assert MIGRATION_FILE.name == "009_create_export_history.sql"

    def test_creates_table_if_not_exists(self, sql: str):
        pattern = re.compile(
            r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+export_history",
            re.IGNORECASE,
        )
        assert pattern.search(sql), "missing CREATE TABLE IF NOT EXISTS"

    def test_all_columns_declared(self, sql: str):
        for col in EXPECTED_COLUMNS:
            assert re.search(
                rf"\b{col}\b", sql
            ), f"column {col!r} not mentioned in migration"

    def test_export_type_check_constraint(self, sql: str):
        # The CHECK must enumerate the three allowed values.
        for value in ("csv", "png", "pdf"):
            assert f"'{value}'" in sql, (
                f"export_type CHECK missing value {value!r}"
            )

    def test_timeframe_check_constraint(self, sql: str):
        for value in ("30d", "90d", "1y", "5y"):
            assert f"'{value}'" in sql, (
                f"timeframe CHECK missing value {value!r}"
            )

    def test_status_check_constraint(self, sql: str):
        for value in ("pending", "completed", "failed"):
            assert f"'{value}'" in sql, (
                f"status CHECK missing value {value!r}"
            )

    def test_jsonb_default_is_empty_array(self, sql: str):
        # The server default for data_types is '[]'::jsonb.
        assert "'[]'::jsonb" in sql

    def test_status_default_is_pending(self, sql: str):
        assert "'pending'" in sql

    def test_created_at_default_is_now(self, sql: str):
        assert re.search(r"now\(\)", sql, re.IGNORECASE)

    def test_three_indexes_declared(self, sql: str):
        for idx_name in EXPECTED_INDEXES:
            assert idx_name in sql, f"index {idx_name!r} missing"

    def test_indexes_use_if_not_exists(self, sql: str):
        # Idempotency: every CREATE INDEX should be IF NOT EXISTS.
        create_indexes = re.findall(
            r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(IF\s+NOT\s+EXISTS\s+)?",
            sql,
            re.IGNORECASE,
        )
        assert create_indexes, "no CREATE INDEX statements found"
        for captured in create_indexes:
            assert captured, (
                "every CREATE INDEX must use IF NOT EXISTS"
            )

    def test_table_comment_present(self, sql: str):
        assert re.search(
            r"COMMENT\s+ON\s+TABLE\s+export_history",
            sql,
            re.IGNORECASE,
        )

    def test_column_comments_present(self, sql: str):
        # Every column except `id` should have a COMMENT ON COLUMN.
        # `id` is a BIGINT PRIMARY KEY and is not commented in
        # migration 009 — see EXPECTED_COMMENTED_COLUMNS.
        for col in EXPECTED_COMMENTED_COLUMNS:
            pattern = re.compile(
                rf"COMMENT\s+ON\s+COLUMN\s+export_history\.{col}\b",
                re.IGNORECASE,
            )
            assert pattern.search(sql), (
                f"missing COMMENT ON COLUMN export_history.{col}"
            )