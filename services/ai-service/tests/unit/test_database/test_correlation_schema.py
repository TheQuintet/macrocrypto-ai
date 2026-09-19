"""Unit tests for the btc_macro_correlation table schema.

These tests verify that the SQLAlchemy Core Table object matches
the migration and the repository's expectations. They do not
require a live database.

Test organization:
    - TestColumns: column names, nullability, types
    - TestPrimaryKey: composite primary key columns
    - TestIndexes: index names and covered columns
    - TestConstants: TABLE_BTC_MACRO_CORRELATION
"""

from sqlalchemy import Float, Integer, String
from sqlalchemy.types import DateTime

from app.database.tables import (
    TABLE_BTC_MACRO_CORRELATION,
    btc_macro_correlation,
    metadata,
)


# ============================================================
# COLUMNS
# ============================================================
class TestColumns:
    """Tests for the btc_macro_correlation table columns."""

    def test_table_name(self) -> None:
        """Test that the table has the expected name."""
        assert btc_macro_correlation.name == "btc_macro_correlation"

    def test_registered_in_metadata(self) -> None:
        """Test that the table is attached to the shared MetaData."""
        assert "btc_macro_correlation" in metadata.tables
        assert (
            metadata.tables["btc_macro_correlation"]
            is btc_macro_correlation
        )

    def test_column_names(self) -> None:
        """Test that all expected columns are present."""
        expected = {
            "indicator_name",
            "window_days",
            "calculated_at",
            "correlation_coefficient",
            "strength",
            "direction",
            "p_value",
            "created_at",
        }
        assert set(btc_macro_correlation.c.keys()) == expected

    def test_indicator_name_not_nullable(self) -> None:
        """Test that indicator_name is NOT NULL."""
        assert (
            btc_macro_correlation.c.indicator_name.nullable is False
        )

    def test_window_days_not_nullable(self) -> None:
        """Test that window_days is NOT NULL."""
        assert btc_macro_correlation.c.window_days.nullable is False

    def test_calculated_at_not_nullable(self) -> None:
        """Test that calculated_at is NOT NULL."""
        assert btc_macro_correlation.c.calculated_at.nullable is False

    def test_coefficient_not_nullable(self) -> None:
        """Test that correlation_coefficient is NOT NULL."""
        assert (
            btc_macro_correlation.c.correlation_coefficient.nullable
            is False
        )

    def test_strength_not_nullable(self) -> None:
        """Test that strength is NOT NULL."""
        assert btc_macro_correlation.c.strength.nullable is False

    def test_direction_not_nullable(self) -> None:
        """Test that direction is NOT NULL."""
        assert btc_macro_correlation.c.direction.nullable is False

    def test_p_value_is_nullable(self) -> None:
        """Test that p_value is nullable.

        A1.2 writes rows before A1.4 computes significance, so
        p_value must accept NULL at insert time.
        """
        assert btc_macro_correlation.c.p_value.nullable is True

    def test_column_types(self) -> None:
        """Test that columns have the expected types."""
        assert isinstance(
            btc_macro_correlation.c.indicator_name.type, String
        )
        assert btc_macro_correlation.c.indicator_name.type.length == 32
        assert isinstance(
            btc_macro_correlation.c.window_days.type, Integer
        )
        assert isinstance(
            btc_macro_correlation.c.correlation_coefficient.type, Float
        )
        assert isinstance(btc_macro_correlation.c.strength.type, String)
        assert btc_macro_correlation.c.strength.type.length == 16
        assert isinstance(btc_macro_correlation.c.direction.type, String)
        assert btc_macro_correlation.c.direction.type.length == 16
        assert isinstance(btc_macro_correlation.c.p_value.type, Float)

    def test_calculated_at_is_tz_aware_datetime(self) -> None:
        """Test that calculated_at is a timezone-aware DateTime."""
        col_type = btc_macro_correlation.c.calculated_at.type
        assert isinstance(col_type, DateTime)
        assert col_type.timezone is True

    def test_created_at_is_tz_aware_datetime(self) -> None:
        """Test that created_at is a timezone-aware DateTime."""
        col_type = btc_macro_correlation.c.created_at.type
        assert isinstance(col_type, DateTime)
        assert col_type.timezone is True


# ============================================================
# PRIMARY KEY
# ============================================================
class TestPrimaryKey:
    """Tests for the composite primary key."""

    def test_composite_pk_columns(self) -> None:
        """Test that the PK is (indicator_name, window_days, calculated_at)."""
        pk_cols = [
            c.name
            for c in btc_macro_correlation.primary_key.columns
        ]
        # SQLAlchemy preserves definition order
        assert pk_cols == [
            "indicator_name",
            "window_days",
            "calculated_at",
        ]

    def test_no_surrogate_id(self) -> None:
        """Test that there is no surrogate id column.

        Unlike prediction_performance and model_performance, this
        table uses the natural composite key; no surrogate id.
        """
        assert "id" not in btc_macro_correlation.c


# ============================================================
# INDEXES
# ============================================================
class TestIndexes:
    """Tests for the btc_macro_correlation indexes."""

    def _index_names(self) -> set:
        """Return the set of index names attached to the table."""
        return {idx.name for idx in btc_macro_correlation.indexes}

    def test_indicator_index_present(self) -> None:
        """Test that the (indicator_name) index exists."""
        assert (
            "idx_btc_macro_correlation_indicator_name"
            in self._index_names()
        )

    def test_window_index_present(self) -> None:
        """Test that the (window_days) index exists."""
        assert (
            "idx_btc_macro_correlation_window_days"
            in self._index_names()
        )

    def test_calculated_at_index_present(self) -> None:
        """Test that the (calculated_at) index exists."""
        assert (
            "idx_btc_macro_correlation_calculated_at"
            in self._index_names()
        )

    def test_composite_index_present(self) -> None:
        """Test that the (indicator, window, calculated_at) index exists."""
        assert (
            "idx_btc_macro_correlation_indicator_window_calc"
            in self._index_names()
        )

    def test_composite_index_column_order(self) -> None:
        """Test that the composite index covers the three business columns."""
        idx = next(
            i
            for i in btc_macro_correlation.indexes
            if i.name
            == "idx_btc_macro_correlation_indicator_window_calc"
        )
        cols = [c.name for c in idx.columns]
        assert cols == [
            "indicator_name",
            "window_days",
            "calculated_at",
        ]

    def test_composite_index_calculated_at_is_desc(self) -> None:
        """Test that the composite index orders calculated_at DESC.

        The common read is "latest N rows for this (indicator,
        window)", so DESC on the trailing column matches the access
        pattern.

        We compile the index to SQL and assert on the trailing
        "DESC" modifier, because SQLAlchemy's Index.columns returns
        the plain Column object rather than the expression that
        carries the ordering modifier.
        """
        from sqlalchemy.schema import CreateIndex
        from sqlalchemy.dialects import postgresql

        idx = next(
            i
            for i in btc_macro_correlation.indexes
            if i.name
            == "idx_btc_macro_correlation_indicator_window_calc"
        )
        compiled = str(
            CreateIndex(idx).compile(dialect=postgresql.dialect())
        )
        assert "indicator_name" in compiled
        assert "window_days" in compiled
        assert "calculated_at DESC" in compiled


# ============================================================
# CONSTANTS
# ============================================================
class TestConstants:
    """Tests for module constants tied to the table."""

    def test_table_constant(self) -> None:
        """Test that TABLE_BTC_MACRO_CORRELATION matches the table name."""
        assert (
            TABLE_BTC_MACRO_CORRELATION == "btc_macro_correlation"
        )