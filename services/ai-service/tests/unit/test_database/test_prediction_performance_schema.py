"""Regression tests for the prediction_performance schema.

Verifies that the prediction_performance table (created by
migration 004) and the btc_predictions.id column (added by
migration 003) match their intended shape:

    - All required columns exist with correct nullability
    - The FK to btc_predictions.id is declared in the SQL
    - CHECK constraints enforce the enum + non-negativity rules
    - Indexes cover the common read patterns
    - The migration runner discovers the new files in order
    - The Core Table's column set matches the migration SQL

These are NOT integration tests — no live Postgres is required.

Test organization:
    - TestPerformanceTableStructure: Core Table columns
    - TestBtcPredictionsIdColumn: btc_predictions.id
    - TestPerformanceMigrationSql: raw SQL content of migration 004
    - TestBtcPredictionsIdMigrationSql: raw SQL content of migration 003
    - TestPredictionIdNullableMigration: migration 005 (T5.2)
    - TestMigrationDiscovery: runner sees all new files
"""

from pathlib import Path

import pytest

from app.database.tables import (
    btc_predictions,
    metadata,
    prediction_performance,
)


# ============================================================
# FIXTURES
# ============================================================
@pytest.fixture(scope="module")
def migrations_dir() -> Path:
    """Return the migrations directory."""
    # services/ai-service/tests/unit/test_database/... → up 3 → ai-service
    service_root = Path(__file__).resolve().parents[3]
    return service_root / "migrations"


@pytest.fixture(scope="module")
def perf_sql(migrations_dir: Path) -> str:
    """Return the text of migration 004."""
    return (migrations_dir / "004_create_prediction_performance.sql").read_text()


@pytest.fixture(scope="module")
def id_sql(migrations_dir: Path) -> str:
    """Return the text of migration 003."""
    return (migrations_dir / "003_add_btc_predictions_id.sql").read_text()


# ============================================================
# CORE TABLE STRUCTURE
# ============================================================
class TestPerformanceTableStructure:
    """Verify the prediction_performance Core Table's shape."""

    def test_table_registered_in_metadata(self) -> None:
        """Test that the table is registered in shared metadata."""
        assert "prediction_performance" in metadata.tables

    def test_all_required_columns_present(self) -> None:
        """Test that every required column exists."""
        required = {
            "id",
            "prediction_id",
            "horizon",
            "model_name",
            "model_version",
            "forecast_date",
            "predicted_price",
            "actual_price",
            "mae",
            "rmse",
            "mape",
            "market_condition",
            "created_at",
        }
        assert required.issubset(set(prediction_performance.c.keys()))

    def test_id_is_primary_key(self) -> None:
        """Test that `id` is the primary key."""
        pk_columns = [col.name for col in prediction_performance.primary_key]
        assert pk_columns == ["id"]

    def test_prediction_id_is_nullable(self) -> None:
        """Test that prediction_id is nullable (backtest rows have NULL)."""
        assert prediction_performance.c.prediction_id.nullable is True

    def test_horizon_is_not_nullable(self) -> None:
        """Test that horizon is NOT NULL."""
        assert prediction_performance.c.horizon.nullable is False

    def test_model_name_is_not_nullable(self) -> None:
        """Test that model_name is NOT NULL."""
        assert prediction_performance.c.model_name.nullable is False

    def test_model_version_is_not_nullable(self) -> None:
        """Test that model_version is NOT NULL."""
        assert prediction_performance.c.model_version.nullable is False

    def test_forecast_date_is_not_nullable(self) -> None:
        """Test that forecast_date is NOT NULL."""
        assert prediction_performance.c.forecast_date.nullable is False

    def test_predicted_price_is_not_nullable(self) -> None:
        """Test that predicted_price is NOT NULL."""
        assert prediction_performance.c.predicted_price.nullable is False

    def test_actual_price_is_not_nullable(self) -> None:
        """Test that actual_price is NOT NULL."""
        assert prediction_performance.c.actual_price.nullable is False

    def test_mae_is_nullable(self) -> None:
        """Test that mae is nullable (populated by T5.2)."""
        assert prediction_performance.c.mae.nullable is True

    def test_rmse_is_nullable(self) -> None:
        """Test that rmse is nullable (populated by T5.2)."""
        assert prediction_performance.c.rmse.nullable is True

    def test_mape_is_nullable(self) -> None:
        """Test that mape is nullable (populated by T5.2)."""
        assert prediction_performance.c.mape.nullable is True

    def test_market_condition_is_nullable(self) -> None:
        """Test that market_condition is nullable (populated by T5.3)."""
        assert prediction_performance.c.market_condition.nullable is True

    def test_horizon_column_length(self) -> None:
        """Test that horizon is wide enough for '24h' and '7d'."""
        assert prediction_performance.c.horizon.type.length >= 3

    def test_model_version_column_length(self) -> None:
        """Test that model_version is wide enough for a semver string."""
        assert prediction_performance.c.model_version.type.length >= 5


# ============================================================
# btc_predictions.id COLUMN
# ============================================================
class TestBtcPredictionsIdColumn:
    """Verify the surrogate id column added to btc_predictions."""

    def test_id_column_exists(self) -> None:
        """Test that btc_predictions has an id column."""
        assert "id" in btc_predictions.c

    def test_id_is_not_nullable(self) -> None:
        """Test that the id column is NOT NULL."""
        assert btc_predictions.c.id.nullable is False

    def test_id_is_bigint(self) -> None:
        """Test that id is BIGINT."""
        # SQLAlchemy BigInteger -> type name contains 'BIGINT'
        type_name = str(btc_predictions.c.id.type).upper()
        assert "BIGINT" in type_name


# ============================================================
# MIGRATION 004 — SQL CONTENT
# ============================================================
class TestPerformanceMigrationSql:
    """Verify the SQL content of migration 004."""

    def test_migration_file_exists(self, migrations_dir: Path) -> None:
        """Test that the file is present."""
        assert (
            migrations_dir / "004_create_prediction_performance.sql"
        ).exists()

    def test_creates_table(self, perf_sql: str) -> None:
        """Test that the table is created."""
        assert "CREATE TABLE IF NOT EXISTS prediction_performance" in perf_sql

    def test_pk_is_bigserial(self, perf_sql: str) -> None:
        """Test that id uses BIGSERIAL."""
        assert "id" in perf_sql
        assert "BIGSERIAL" in perf_sql

    def test_fk_to_btc_predictions(self, perf_sql: str) -> None:
        """Test that prediction_id is a FK to btc_predictions(id)."""
        assert "REFERENCES btc_predictions(id)" in perf_sql

    def test_fk_on_delete_cascade(self, perf_sql: str) -> None:
        """Test that the FK uses ON DELETE CASCADE."""
        assert "ON DELETE CASCADE" in perf_sql

    def test_market_condition_check(self, perf_sql: str) -> None:
        """Test that market_condition has a CHECK constraint."""
        assert "prediction_performance_market_condition_valid" in perf_sql
        for cond in ("bull", "bear", "volatile", "neutral"):
            assert f"'{cond}'" in perf_sql

    def test_mae_non_negative_check(self, perf_sql: str) -> None:
        """Test that mae has a non-negative CHECK."""
        assert "prediction_performance_mae_non_negative" in perf_sql

    def test_rmse_non_negative_check(self, perf_sql: str) -> None:
        """Test that rmse has a non-negative CHECK."""
        assert "prediction_performance_rmse_non_negative" in perf_sql

    def test_mape_non_negative_check(self, perf_sql: str) -> None:
        """Test that mape has a non-negative CHECK."""
        assert "prediction_performance_mape_non_negative" in perf_sql

    def test_prices_positive_check(self, perf_sql: str) -> None:
        """Test that prices have a positive CHECK."""
        assert "prediction_performance_prices_positive" in perf_sql

    def test_horizon_model_index(self, perf_sql: str) -> None:
        """Test that the horizon+model+date index is created."""
        assert "idx_prediction_performance_horizon_model_date" in perf_sql

    def test_forecast_date_index(self, perf_sql: str) -> None:
        """Test that the forecast_date index is created."""
        assert "idx_prediction_performance_forecast_date" in perf_sql

    def test_prediction_id_index(self, perf_sql: str) -> None:
        """Test that the FK-lookup index is created."""
        assert "idx_prediction_performance_prediction_id" in perf_sql

    def test_market_condition_partial_index(self, perf_sql: str) -> None:
        """Test that the market_condition partial index is created."""
        assert "idx_prediction_performance_market_condition" in perf_sql
        # Partial: only where market_condition IS NOT NULL
        assert "WHERE market_condition IS NOT NULL" in perf_sql


# ============================================================
# MIGRATION 003 — SQL CONTENT
# ============================================================
class TestBtcPredictionsIdMigrationSql:
    """Verify the SQL content of migration 003."""

    def test_migration_file_exists(self, migrations_dir: Path) -> None:
        """Test that the file is present."""
        assert (migrations_dir / "003_add_btc_predictions_id.sql").exists()

    def test_adds_id_column(self, id_sql: str) -> None:
        """Test that the id column is added."""
        assert "ADD COLUMN IF NOT EXISTS id" in id_sql

    def test_id_is_bigserial(self, id_sql: str) -> None:
        """Test that id uses BIGSERIAL."""
        assert "BIGSERIAL" in id_sql

    def test_unique_constraint(self, id_sql: str) -> None:
        """Test that the id column gets a UNIQUE constraint."""
        assert "btc_predictions_id_key" in id_sql
        assert "UNIQUE (id)" in id_sql

    def test_index_created(self, id_sql: str) -> None:
        """Test that an index on id is created."""
        assert "idx_btc_predictions_id" in id_sql


# ============================================================
# MIGRATION 005 — prediction_id NULLABLE
# ============================================================
class TestPredictionIdNullableMigration:
    """Verify migration 005 relaxes prediction_id's NOT NULL."""

    def test_migration_file_exists(self, migrations_dir: Path) -> None:
        """Test that the file is present."""
        assert (
            migrations_dir / "005_make_prediction_id_nullable.sql"
        ).exists()

    def test_drops_not_null(self, migrations_dir: Path) -> None:
        """Test that the migration drops NOT NULL on prediction_id."""
        sql = (
            migrations_dir / "005_make_prediction_id_nullable.sql"
        ).read_text()
        assert "ALTER COLUMN prediction_id DROP NOT NULL" in sql

    def test_runner_finds_it(self) -> None:
        """Test that the migration runner discovers migration 005."""
        from app.database.migrations_runner import discover_migrations

        service_root = Path(__file__).resolve().parents[3]
        migrations_dir = service_root / "migrations"
        names = [f.name for f in discover_migrations(migrations_dir)]
        assert "005_make_prediction_id_nullable.sql" in names


# ============================================================
# MIGRATION DISCOVERY
# ============================================================
class TestMigrationDiscovery:
    """Verify the migration runner discovers the new files."""

    def test_runner_finds_both_new_migrations(self) -> None:
        """Test that discover_migrations finds 003, 004, and 005."""
        from app.database.migrations_runner import discover_migrations

        # Build the path relative to this test file
        service_root = Path(__file__).resolve().parents[3]
        migrations_dir = service_root / "migrations"

        files = discover_migrations(migrations_dir)
        names = [f.name for f in files]

        assert "003_add_btc_predictions_id.sql" in names
        assert "004_create_prediction_performance.sql" in names
        assert "005_make_prediction_id_nullable.sql" in names

    def test_runner_sorts_correctly(self) -> None:
        """Test that migrations appear in lexicographic order."""
        from app.database.migrations_runner import discover_migrations

        service_root = Path(__file__).resolve().parents[3]
        migrations_dir = service_root / "migrations"

        files = discover_migrations(migrations_dir)
        names = [f.name for f in files]

        # 003 must come before 004, 004 before 005
        assert names.index("003_add_btc_predictions_id.sql") < names.index(
            "004_create_prediction_performance.sql"
        )
        assert names.index("004_create_prediction_performance.sql") < names.index(
            "005_make_prediction_id_nullable.sql"
        )