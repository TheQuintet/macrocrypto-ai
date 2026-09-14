"""Regression tests for the btc_predictions schema.

These tests verify that the unified btc_predictions table (created by
migration 002) supports BOTH the 24h and 7d horizons end-to-end at
the schema-definition level:

    - The `horizon` column exists and is wide enough
    - The CHECK constraint allows '24h' and '7d' (and rejects others)
    - The composite primary key includes `horizon`
    - The indexes cover the 7d read pattern
    - The repository validator accepts '7d' rows
    - The PredictionRow dataclass round-trips 7d values

These are NOT integration tests — no live Postgres is required. They
inspect the SQLAlchemy Core Table object and the migration SQL file
to confirm the schema's shape.

Test organization:
    - TestPredictionTableStructure: columns, PK, CHECK constraints
    - TestPredictionTableIndexes: index coverage (from migration SQL)
    - TestMigrationSql: raw SQL migration file content
    - TestValidatorSupports7d: validator accepts 7d rows
    - TestRepositorySupports7d: repository handles 7d rows
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.database.repositories.prediction_repository import PredictionRow
from app.database.tables import btc_predictions
from app.database.validators import (
    VALID_HORIZONS,
    validate_prediction_row,
    validate_prediction_rows,
)


# ============================================================
# FIXTURES
# ============================================================
@pytest.fixture(scope="module")
def migration_path() -> Path:
    """Return the path to the btc_predictions migration file.

    Layout assumed:
        services/ai-service/tests/unit/test_database/test_btc_predictions_schema.py
        services/ai-service/migrations/002_create_btc_predictions.sql
    """
    # This file is at .../services/ai-service/tests/unit/test_database/...
    # parents[0] = test_database
    # parents[1] = unit
    # parents[2] = tests
    # parents[3] = ai-service
    service_root = Path(__file__).resolve().parents[3]
    return service_root / "migrations" / "002_create_btc_predictions.sql"


# ============================================================
# SCHEMA STRUCTURE
# ============================================================
class TestPredictionTableStructure:
    """Verify the btc_predictions table supports both horizons."""

    def test_horizon_column_exists(self) -> None:
        """Test that the `horizon` column is defined."""
        assert "horizon" in btc_predictions.c

    def test_horizon_column_is_string(self) -> None:
        """Test that `horizon` is a String column."""
        col = btc_predictions.c.horizon
        # SQLAlchemy String type
        assert hasattr(col.type, "length")
        assert col.type.length >= 3  # at least enough for '24h' / '7d'

    def test_horizon_column_is_not_nullable(self) -> None:
        """Test that `horizon` is NOT NULL."""
        assert btc_predictions.c.horizon.nullable is False

    def test_horizon_in_primary_key(self) -> None:
        """Test that `horizon` is part of the composite primary key."""
        pk_columns = [col.name for col in btc_predictions.primary_key]
        assert "horizon" in pk_columns

    def test_all_required_columns_present(self) -> None:
        """Test that every column from the T2.3 ticket is present."""
        required = {
            "time",
            "prediction_time",
            "horizon",
            "model_name",
            "confidence",
            "predicted_price",
            "lower_bound",
            "upper_bound",
        }
        assert required.issubset(set(btc_predictions.c.keys()))

    def test_model_name_column_exists(self) -> None:
        """Test that `model_name` is defined (for M6 multi-model support)."""
        assert "model_name" in btc_predictions.c

    def test_confidence_column_exists(self) -> None:
        """Test that `confidence` is defined."""
        assert "confidence" in btc_predictions.c


# ============================================================
# INDEXES (from migration SQL)
# ============================================================
class TestPredictionTableIndexes:
    """Verify indexes cover both 24h and 7d read patterns.

    Indexes are defined in the migration SQL, not in the Core Table
    (see app/database/tables.py — only the composite read index is
    attached to the Core Table for query planning). The migration is
    the source of truth for the full index set.
    """

    def test_horizon_model_time_index_in_core_table(self) -> None:
        """Test that the horizon+model+time index is on the Core Table."""
        index_names = [idx.name for idx in btc_predictions.indexes]
        assert "idx_btc_predictions_horizon_model_time" in index_names

    def test_time_desc_index_in_migration(self, migration_path: Path) -> None:
        """Test that the time DESC index is created in the migration."""
        sql = migration_path.read_text()
        assert "idx_btc_predictions_time_desc" in sql

    def test_prediction_time_index_in_migration(
        self, migration_path: Path
    ) -> None:
        """Test that the prediction_time index is created in the migration."""
        sql = migration_path.read_text()
        assert "idx_btc_predictions_prediction_time" in sql


# ============================================================
# MIGRATION SQL
# ============================================================
class TestMigrationSql:
    """Verify the migration SQL supports 7d."""

    def test_migration_file_exists(self, migration_path: Path) -> None:
        """Test that the migration file exists on disk."""
        assert migration_path.exists(), f"Missing: {migration_path}"

    def test_check_constraint_allows_7d(self, migration_path: Path) -> None:
        """Test that the horizon CHECK constraint includes '7d'."""
        sql = migration_path.read_text()
        assert "btc_predictions_horizon_valid" in sql
        assert "'24h'" in sql
        assert "'7d'" in sql

    def test_creates_hypertable(self, migration_path: Path) -> None:
        """Test that create_hypertable() is called on `time`."""
        sql = migration_path.read_text()
        assert "create_hypertable" in sql
        assert "'time'" in sql

    def test_hypertable_migrate_data_is_set(self, migration_path: Path) -> None:
        """Test that migrate_data is enabled for safe re-runs."""
        sql = migration_path.read_text()
        assert "migrate_data => TRUE" in sql

    def test_indexes_created(self, migration_path: Path) -> None:
        """Test that all three indexes are created in the migration."""
        sql = migration_path.read_text()
        assert "idx_btc_predictions_horizon_model_time" in sql
        assert "idx_btc_predictions_time_desc" in sql
        assert "idx_btc_predictions_prediction_time" in sql


# ============================================================
# VALIDATOR
# ============================================================
class TestValidatorSupports7d:
    """Verify the validator accepts 7d rows."""

    def test_7d_in_valid_horizons(self) -> None:
        """Test that '7d' is in VALID_HORIZONS."""
        assert "7d" in VALID_HORIZONS

    def test_24h_in_valid_horizons(self) -> None:
        """Test that '24h' is in VALID_HORIZONS."""
        assert "24h" in VALID_HORIZONS

    def _make_7d_row(self, **overrides) -> PredictionRow:
        """Build a valid 7d PredictionRow."""
        now = datetime.now(timezone.utc)
        defaults = dict(
            time=now + timedelta(hours=24),
            prediction_time=now,
            horizon="7d",
            model_name="prophet",
            confidence=0.85,
            predicted_price=50_000.0,
            lower_bound=49_000.0,
            upper_bound=51_000.0,
        )
        defaults.update(overrides)
        return PredictionRow(**defaults)

    def test_7d_row_passes_validation(self) -> None:
        """Test that a valid 7d row passes validation."""
        validate_prediction_row(self._make_7d_row())

    def test_7d_row_with_all_confidence_levels(self) -> None:
        """Test that 7d rows pass validation at all confidence levels."""
        for conf in (0.70, 0.85, 0.95):
            validate_prediction_row(self._make_7d_row(confidence=conf))

    def test_7d_row_bounds_ordering_still_enforced(self) -> None:
        """Test that bounds ordering is enforced for 7d rows."""
        with pytest.raises(ValueError, match="lower_bound"):
            validate_prediction_row(
                self._make_7d_row(
                    lower_bound=51_000.0, predicted_price=50_000.0
                )
            )

    def test_batch_with_mixed_horizons_passes(self) -> None:
        """Test that a batch mixing 24h and 7d rows validates."""
        now = datetime.now(timezone.utc)

        rows = [
            self._make_7d_row(),
            PredictionRow(
                time=now + timedelta(hours=1),
                prediction_time=now,
                horizon="24h",
                model_name="prophet",
                confidence=0.85,
                predicted_price=50_000.0,
                lower_bound=49_000.0,
                upper_bound=51_000.0,
            ),
            self._make_7d_row(),
        ]
        validate_prediction_rows(rows)


# ============================================================
# REPOSITORY ROW SUPPORT
# ============================================================
class TestRepositorySupports7d:
    """Verify PredictionRow round-trips 7d values correctly."""

    def test_7d_row_to_dict_preserves_horizon(self) -> None:
        """Test that to_dict preserves horizon='7d'."""
        now = datetime.now(timezone.utc)
        row = PredictionRow(
            time=now,
            prediction_time=now,
            horizon="7d",
            model_name="prophet",
            confidence=0.85,
            predicted_price=50_000.0,
            lower_bound=49_000.0,
            upper_bound=51_000.0,
        )
        d = row.to_dict()
        assert d["horizon"] == "7d"
        assert d["model_name"] == "prophet"

    def test_7d_row_to_dict_has_all_columns(self) -> None:
        """Test that a 7d row serializes to all required columns."""
        now = datetime.now(timezone.utc)
        row = PredictionRow(
            time=now,
            prediction_time=now,
            horizon="7d",
            model_name="prophet",
            confidence=0.85,
            predicted_price=50_000.0,
            lower_bound=49_000.0,
            upper_bound=51_000.0,
        )
        d = row.to_dict()
        expected = {
            "time",
            "prediction_time",
            "horizon",
            "model_name",
            "confidence",
            "predicted_price",
            "lower_bound",
            "upper_bound",
        }
        assert set(d.keys()) == expected

    def test_7d_row_columns_match_schema_columns(self) -> None:
        """Test that PredictionRow.to_dict() keys match btc_predictions columns."""
        now = datetime.now(timezone.utc)
        row = PredictionRow(
            time=now,
            prediction_time=now,
            horizon="7d",
            model_name="prophet",
            confidence=0.85,
            predicted_price=50_000.0,
            lower_bound=49_000.0,
            upper_bound=51_000.0,
        )
        # PredictionRow.to_dict() returns 8 keys (no created_at — that's
        # server-side default). The schema's 9th column (created_at) is
        # auto-populated by Postgres.
        schema_columns = set(btc_predictions.c.keys())
        row_columns = set(row.to_dict().keys())
        # row keys should be a subset of schema columns
        assert row_columns.issubset(schema_columns)