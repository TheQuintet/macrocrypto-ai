"""Unit tests for the model_performance table schema.

These tests verify that the SQLAlchemy Core Table object matches
the migration and the repository's expectations. They do not
require a live database.

Test organization:
    - TestColumns: column names, nullability, types
    - TestIndexes: index names and covered columns
    - TestConstants: TABLE_MODEL_PERFORMANCE
"""

from sqlalchemy import Float, Integer, String
from sqlalchemy.types import DateTime

from app.database.tables import (
    TABLE_MODEL_PERFORMANCE,
    metadata,
    model_performance,
)


# ============================================================
# COLUMNS
# ============================================================
class TestColumns:
    """Tests for the model_performance table columns."""

    def test_table_name(self) -> None:
        """Test that the table has the expected name."""
        assert model_performance.name == "model_performance"

    def test_registered_in_metadata(self) -> None:
        """Test that the table is attached to the shared MetaData."""
        assert "model_performance" in metadata.tables
        assert metadata.tables["model_performance"] is model_performance

    def test_column_names(self) -> None:
        """Test that all expected columns are present."""
        expected = {
            "id",
            "model_name",
            "horizon",
            "mae",
            "rmse",
            "mape",
            "directional_accuracy",
            "sample_size",
            "calculated_at",
            "created_at",
        }
        assert set(model_performance.c.keys()) == expected

    def test_id_is_primary_key(self) -> None:
        """Test that id is the primary key."""
        assert model_performance.c.id.primary_key is True

    def test_model_name_not_nullable(self) -> None:
        """Test that model_name is NOT NULL."""
        assert model_performance.c.model_name.nullable is False

    def test_horizon_not_nullable(self) -> None:
        """Test that horizon is NOT NULL."""
        assert model_performance.c.horizon.nullable is False

    def test_sample_size_not_nullable(self) -> None:
        """Test that sample_size is NOT NULL."""
        assert model_performance.c.sample_size.nullable is False

    def test_calculated_at_not_nullable(self) -> None:
        """Test that calculated_at is NOT NULL."""
        assert model_performance.c.calculated_at.nullable is False

    def test_metric_columns_are_nullable(self) -> None:
        """Test that all four metric columns are nullable.

        Not every aggregation run produces every metric —
        directional_accuracy in particular requires ground truth
        that may not always be available.
        """
        for name in ("mae", "rmse", "mape", "directional_accuracy"):
            assert model_performance.c[name].nullable is True, (
                f"{name} should be nullable"
            )

    def test_metric_column_types(self) -> None:
        """Test that metric columns are Float."""
        for name in ("mae", "rmse", "mape", "directional_accuracy"):
            assert isinstance(
                model_performance.c[name].type, Float
            ), f"{name} should be Float"

    def test_sample_size_type(self) -> None:
        """Test that sample_size is Integer."""
        assert isinstance(
            model_performance.c.sample_size.type, Integer
        )

    def test_string_lengths(self) -> None:
        """Test that string columns have the expected lengths."""
        assert isinstance(model_performance.c.model_name.type, String)
        assert model_performance.c.model_name.type.length == 64
        assert isinstance(model_performance.c.horizon.type, String)
        assert model_performance.c.horizon.type.length == 8

    def test_calculated_at_is_tz_aware_datetime(self) -> None:
        """Test that calculated_at is a timezone-aware DateTime."""
        col_type = model_performance.c.calculated_at.type
        assert isinstance(col_type, DateTime)
        assert col_type.timezone is True

    def test_created_at_is_tz_aware_datetime(self) -> None:
        """Test that created_at is a timezone-aware DateTime."""
        col_type = model_performance.c.created_at.type
        assert isinstance(col_type, DateTime)
        assert col_type.timezone is True


# ============================================================
# INDEXES
# ============================================================
class TestIndexes:
    """Tests for the model_performance indexes."""

    def _index_names(self) -> set:
        """Return the set of index names attached to the table."""
        return {idx.name for idx in model_performance.indexes}

    def test_model_name_index_present(self) -> None:
        """Test that the (model_name) index exists."""
        assert "idx_model_performance_model_name" in self._index_names()

    def test_horizon_index_present(self) -> None:
        """Test that the (horizon) index exists."""
        assert "idx_model_performance_horizon" in self._index_names()

    def test_calculated_at_index_present(self) -> None:
        """Test that the (calculated_at) index exists."""
        assert "idx_model_performance_calculated_at" in self._index_names()

    def test_composite_index_present(self) -> None:
        """Test that the (model_name, horizon, calculated_at) index exists."""
        assert (
            "idx_model_performance_model_horizon_calc"
            in self._index_names()
        )

    def test_composite_index_column_order(self) -> None:
        """Test that the composite index covers model, horizon, calculated_at."""
        idx = next(
            i
            for i in model_performance.indexes
            if i.name == "idx_model_performance_model_horizon_calc"
        )
        cols = [c.name for c in idx.columns]
        assert cols == ["model_name", "horizon", "calculated_at"]

    def test_composite_index_calculated_at_is_desc(self) -> None:
        """Test that the composite index orders calculated_at DESC.

        The common read is "latest N rows for this (model, horizon)",
        so DESC on the trailing column matches the access pattern.

        We compile the index to SQL and assert on the trailing
        "DESC" modifier, because SQLAlchemy's Index.columns returns
        the plain Column object rather than the expression that
        carries the ordering modifier.
        """
        from sqlalchemy.schema import CreateIndex
        from sqlalchemy.dialects import postgresql

        idx = next(
            i
            for i in model_performance.indexes
            if i.name == "idx_model_performance_model_horizon_calc"
        )
        compiled = str(
            CreateIndex(idx).compile(dialect=postgresql.dialect())
        )
        # The composite index must include all three columns in order
        assert "model_name" in compiled
        assert "horizon" in compiled
        assert "calculated_at" in compiled
        # The trailing column must be DESC — the modifier appears
        # directly after calculated_at in the compiled SQL.
        assert "calculated_at DESC" in compiled


# ============================================================
# CONSTANTS
# ============================================================
class TestConstants:
    """Tests for module constants tied to the table."""

    def test_table_constant(self) -> None:
        """Test that TABLE_MODEL_PERFORMANCE matches the table name."""
        assert TABLE_MODEL_PERFORMANCE == "model_performance"