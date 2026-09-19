"""Schema-level tests for the historical_event_impacts table (A5.1).

These tests verify the *shape* of the Core Table and the migration
file — column names, types, nullability, defaults, indexes, and the
CHECK constraints / comments in the SQL. They do not touch a live
database; they inspect the SQLAlchemy metadata and read the
migration file as text.
"""

import re
from pathlib import Path

import pytest
from sqlalchemy import BigInteger, Date, DateTime, Float, String

from app.database.tables import (
    TABLE_HISTORICAL_EVENT_IMPACTS,
    historical_event_impacts,
    metadata,
)


# ============================================================
# CONSTANTS
# ============================================================
MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "migrations"
MIGRATION_FILE = MIGRATIONS_DIR / "010_create_historical_event_impacts.sql"

EXPECTED_COLUMNS = [
    "id",
    "event_name",
    "event_date",
    "impact_level",
    "btc_price_before",
    "btc_price_after",
    "price_change_percent",
    "volatility",
    "direction",
    "created_at",
]

# Columns that must carry a COMMENT ON COLUMN in the migration.
# `id` is deliberately excluded: a BIGSERIAL PRIMARY KEY is
# self-documenting, and migration 010 does not comment it.
EXPECTED_COMMENTED_COLUMNS = [
    "event_name",
    "event_date",
    "impact_level",
    "btc_price_before",
    "btc_price_after",
    "price_change_percent",
    "volatility",
    "direction",
    "created_at",
]

EXPECTED_INDEXES = {
    "idx_historical_event_impacts_event_name",
    "idx_historical_event_impacts_event_date",
}


# ============================================================
# MODULE-LEVEL FIXTURE
# ============================================================
@pytest.fixture(scope="module")
def sql() -> str:
    """Read the migration file once per module and share it."""
    assert MIGRATION_FILE.exists(), (
        f"Migration file not found: {MIGRATION_FILE}"
    )
    return MIGRATION_FILE.read_text(encoding="utf-8")


# ============================================================
# CORE TABLE
# ============================================================
class TestHistoricalEventImpactsTable:
    """Shape of the Core Table object in app.database.tables."""

    def test_constant_name(self):
        assert TABLE_HISTORICAL_EVENT_IMPACTS == "historical_event_impacts"

    def test_table_name(self):
        assert historical_event_impacts.name == "historical_event_impacts"

    def test_registered_in_metadata(self):
        assert "historical_event_impacts" in metadata.tables
        assert (
            metadata.tables["historical_event_impacts"]
            is historical_event_impacts
        )

    def test_column_names_and_order(self):
        assert (
            [c.name for c in historical_event_impacts.columns]
            == EXPECTED_COLUMNS
        )

    def test_id_is_bigint_primary_key(self):
        col = historical_event_impacts.c.id
        assert isinstance(col.type, BigInteger)
        assert col.primary_key is True
        assert col.nullable is False

    def test_event_name_is_not_null_varchar_64(self):
        col = historical_event_impacts.c.event_name
        assert isinstance(col.type, String)
        assert col.type.length == 64
        assert col.nullable is False

    def test_event_date_is_not_null_date(self):
        col = historical_event_impacts.c.event_date
        assert isinstance(col.type, Date)
        # Date columns have no timezone attribute; confirm we are
        # not accidentally working with DateTime.
        assert not isinstance(col.type, DateTime)
        assert col.nullable is False

    def test_impact_level_is_not_null_varchar_16(self):
        col = historical_event_impacts.c.impact_level
        assert isinstance(col.type, String)
        assert col.type.length == 16
        assert col.nullable is False

    def test_btc_price_before_is_not_null_float(self):
        col = historical_event_impacts.c.btc_price_before
        assert isinstance(col.type, Float)
        assert col.nullable is False

    def test_btc_price_after_is_not_null_float(self):
        col = historical_event_impacts.c.btc_price_after
        assert isinstance(col.type, Float)
        assert col.nullable is False

    def test_price_change_percent_is_not_null_float(self):
        col = historical_event_impacts.c.price_change_percent
        assert isinstance(col.type, Float)
        assert col.nullable is False

    def test_volatility_is_not_null_float(self):
        col = historical_event_impacts.c.volatility
        assert isinstance(col.type, Float)
        assert col.nullable is False

    def test_direction_is_not_null_varchar_16(self):
        col = historical_event_impacts.c.direction
        assert isinstance(col.type, String)
        assert col.type.length == 16
        assert col.nullable is False

    def test_created_at_is_not_null_timestamptz(self):
        col = historical_event_impacts.c.created_at
        assert isinstance(col.type, DateTime)
        assert col.type.timezone is True
        assert col.nullable is False

    def test_indexes_present(self):
        names = {idx.name for idx in historical_event_impacts.indexes}
        assert EXPECTED_INDEXES.issubset(names)

    def test_event_name_index(self):
        idx = next(
            i for i in historical_event_impacts.indexes
            if i.name == "idx_historical_event_impacts_event_name"
        )
        assert [c.name for c in idx.columns] == ["event_name"]

    def test_event_date_index(self):
        idx = next(
            i for i in historical_event_impacts.indexes
            if i.name == "idx_historical_event_impacts_event_date"
        )
        assert [c.name for c in idx.columns] == ["event_date"]


# ============================================================
# MIGRATION FILE
# ============================================================
class TestHistoricalEventImpactsMigration:
    """Content of migrations/010_create_historical_event_impacts.sql."""

    def test_file_exists(self):
        assert MIGRATION_FILE.exists()
        assert (
            MIGRATION_FILE.name
            == "010_create_historical_event_impacts.sql"
        )

    def test_creates_table_if_not_exists(self, sql: str):
        pattern = re.compile(
            r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+historical_event_impacts",
            re.IGNORECASE,
        )
        assert pattern.search(sql), "missing CREATE TABLE IF NOT EXISTS"

    def test_all_columns_declared(self, sql: str):
        for col in EXPECTED_COLUMNS:
            assert re.search(
                rf"\b{col}\b", sql
            ), f"column {col!r} not mentioned in migration"

    def test_impact_level_check_constraint(self, sql: str):
        for value in ("high", "medium", "low"):
            assert f"'{value}'" in sql, (
                f"impact_level CHECK missing value {value!r}"
            )

    def test_direction_check_constraint(self, sql: str):
        for value in ("up", "down", "neutral"):
            assert f"'{value}'" in sql, (
                f"direction CHECK missing value {value!r}"
            )

    def test_price_before_positive_check(self, sql: str):
        assert re.search(
            r"CHECK\s*\(\s*btc_price_before\s*>\s*0\s*\)",
            sql,
            re.IGNORECASE,
        )

    def test_price_after_positive_check(self, sql: str):
        assert re.search(
            r"CHECK\s*\(\s*btc_price_after\s*>\s*0\s*\)",
            sql,
            re.IGNORECASE,
        )

    def test_volatility_non_negative_check(self, sql: str):
        assert re.search(
            r"CHECK\s*\(\s*volatility\s*>=\s*0\s*\)",
            sql,
            re.IGNORECASE,
        )

    def test_unique_name_date_constraint(self, sql: str):
        assert re.search(
            r"UNIQUE\s*\(\s*event_name\s*,\s*event_date\s*\)",
            sql,
            re.IGNORECASE,
        )

    def test_three_indexes_declared(self, sql: str):
        for idx_name in EXPECTED_INDEXES:
            assert idx_name in sql, f"index {idx_name!r} missing"

    def test_indexes_use_if_not_exists(self, sql: str):
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
            r"COMMENT\s+ON\s+TABLE\s+historical_event_impacts",
            sql,
            re.IGNORECASE,
        )

    def test_column_comments_present(self, sql: str):
        for col in EXPECTED_COMMENTED_COLUMNS:
            pattern = re.compile(
                rf"COMMENT\s+ON\s+COLUMN\s+historical_event_impacts\.{col}\b",
                re.IGNORECASE,
            )
            assert pattern.search(sql), (
                f"missing COMMENT ON COLUMN historical_event_impacts.{col}"
            )