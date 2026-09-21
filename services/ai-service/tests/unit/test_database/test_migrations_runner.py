"""Unit tests for the migrations runner.

These tests exercise the pure helper functions
(discover_migrations, _default_migrations_dir) without a live DB.
Integration with a real Postgres is intentionally out of scope for
T1.3 — see T1.6 for end-to-end migration tests.

Test organization:
    - TestDiscoverMigrations: file discovery + sorting
    - TestDefaultMigrationsDir: default path resolution
    - TestMigrationContent: sanity-check the bundled .sql files
"""

import os
from pathlib import Path

import pytest

from app.database.migrations_runner import (
    _default_migrations_dir,
    discover_migrations,
)


# ============================================================
# DISCOVERY TESTS
# ============================================================
class TestDiscoverMigrations:
    """Tests for discover_migrations()."""

    def test_missing_directory_returns_empty(self, tmp_path: Path) -> None:
        """Test that a missing directory returns an empty list."""
        missing = tmp_path / "does_not_exist"
        assert discover_migrations(missing) == []

    def test_empty_directory_returns_empty(self, tmp_path: Path) -> None:
        """Test that an empty directory returns an empty list."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        assert discover_migrations(empty_dir) == []

    def test_finds_only_sql_files(self, tmp_path: Path) -> None:
        """Test that only .sql files are discovered."""
        (tmp_path / "001_a.sql").write_text("SELECT 1;")
        (tmp_path / "002_b.sql").write_text("SELECT 2;")
        (tmp_path / "not_sql.txt").write_text("ignored")
        (tmp_path / "readme.md").write_text("ignored")

        files = discover_migrations(tmp_path)
        names = [f.name for f in files]

        assert names == ["001_a.sql", "002_b.sql"]

    def test_sorts_lexicographically(self, tmp_path: Path) -> None:
        """Test that files are returned in lexicographic order."""
        # Write in a scrambled order
        for name in ["003_c.sql", "001_a.sql", "002_b.sql"]:
            (tmp_path / name).write_text("SELECT 1;")

        files = discover_migrations(tmp_path)
        names = [f.name for f in files]

        assert names == ["001_a.sql", "002_b.sql", "003_c.sql"]

    def test_returns_path_objects(self, tmp_path: Path) -> None:
        """Test that the function returns Path objects."""
        (tmp_path / "001_a.sql").write_text("SELECT 1;")
        files = discover_migrations(tmp_path)
        assert all(isinstance(f, Path) for f in files)

    def test_file_instead_of_directory_returns_empty(
        self, tmp_path: Path
    ) -> None:
        """Test that a file path (not a directory) returns empty."""
        fake_dir = tmp_path / "not_a_dir"
        fake_dir.write_text("I'm a file, not a directory")
        assert discover_migrations(fake_dir) == []


# ============================================================
# DEFAULT DIR TESTS
# ============================================================
class TestDefaultMigrationsDir:
    """Tests for _default_migrations_dir()."""

    def test_returns_expected_path(self) -> None:
        """Test that the default dir resolves to services/ai-service/migrations."""
        result = _default_migrations_dir()
        assert isinstance(result, Path)
        assert result.name == "migrations"

    def test_path_is_below_service_root(self) -> None:
        """Test that the path ends with 'services/ai-service/migrations'."""
        result = _default_migrations_dir()
        parts = result.parts
        assert "services" in parts
        assert "ai-service" in parts
        assert parts[-1] == "migrations"


# ============================================================
# BUNDLED MIGRATION CONTENT TESTS
# ============================================================
class TestMigrationContent:
    """Sanity checks on the bundled migration files.

    These tests don't connect to a DB — they just verify the SQL
    files exist and contain the expected statements. This catches
    accidental deletions or typos in migration filenames.

    The fixture is class-scoped and decorated with @classmethod per
    pytest's recommended pattern for class-scoped state.
    """

    @pytest.fixture(scope="class")
    @classmethod
    def migrations_dir(cls) -> Path:
        """Return the real migrations directory."""
        return _default_migrations_dir()

    def test_001_exists(self, migrations_dir: Path) -> None:
        """Test that migration 001 exists."""
        assert (migrations_dir / "001_create_schema_migrations.sql").exists()

    def test_002_exists(self, migrations_dir: Path) -> None:
        """Test that migration 002 exists."""
        assert (migrations_dir / "002_create_btc_predictions.sql").exists()

    def test_001_creates_schema_migrations(
        self, migrations_dir: Path
    ) -> None:
        """Test that migration 001 creates the schema_migrations table."""
        content = (migrations_dir / "001_create_schema_migrations.sql").read_text()
        assert "CREATE TABLE IF NOT EXISTS schema_migrations" in content

    def test_002_creates_btc_predictions(
        self, migrations_dir: Path
    ) -> None:
        """Test that migration 002 creates the btc_predictions table."""
        content = (migrations_dir / "002_create_btc_predictions.sql").read_text()
        assert "CREATE TABLE IF NOT EXISTS btc_predictions" in content

    def test_002_converts_to_hypertable(
        self, migrations_dir: Path
    ) -> None:
        """Test that migration 002 calls create_hypertable()."""
        content = (migrations_dir / "002_create_btc_predictions.sql").read_text()
        assert "create_hypertable" in content

    def test_002_has_indexes(self, migrations_dir: Path) -> None:
        """Test that migration 002 creates the expected indexes."""
        content = (migrations_dir / "002_create_btc_predictions.sql").read_text()
        assert "idx_btc_predictions_horizon_model_time" in content
        assert "idx_btc_predictions_time_desc" in content
        assert "idx_btc_predictions_prediction_time" in content

    def test_002_has_check_constraints(self, migrations_dir: Path) -> None:
        """Test that migration 002 includes the CHECK constraints."""
        content = (migrations_dir / "002_create_btc_predictions.sql").read_text()
        assert "btc_predictions_bounds_ordered" in content
        assert "btc_predictions_horizon_valid" in content
        assert "btc_predictions_confidence_valid" in content

    def test_discover_finds_both_files(self, migrations_dir: Path) -> None:
        """Test that discovery finds both bundled migrations."""
        files = discover_migrations(migrations_dir)
        names = [f.name for f in files]
        assert "001_create_schema_migrations.sql" in names
        assert "002_create_btc_predictions.sql" in names