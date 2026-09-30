"""Tests for the SQLAlchemy base model."""

from datetime import datetime

from sqlalchemy import DateTime, Integer

from app.models.base import Base


class BaseTestUser(Base):
    """Test model for standard table-name generation."""

    pass


class BaseTestAPIKey(Base):
    """Test model for acronym table-name generation."""

    pass


class BaseTestStatus(Base):
    """Test model for names ending in 's'."""

    pass


class BaseTestBox(Base):
    """Test model for names ending in 'x'."""

    pass


class BaseTestBranch(Base):
    """Test model for names ending in 'ch'."""

    pass


class BaseTestDish(Base):
    """Test model for names ending in 'sh'."""

    pass


class TestBase:
    """Test common SQLAlchemy Base model functionality."""

    def test_base_is_abstract(self):
        """Test that Base is configured as an abstract model."""
        assert Base.__abstract__ is True

    def test_common_columns_exist(self):
        """Test that common columns are inherited by models."""
        columns = BaseTestUser.__table__.c

        assert "id" in columns
        assert "created_at" in columns
        assert "updated_at" in columns

    def test_id_column_configuration(self):
        """Test the common ID column configuration."""
        column = BaseTestUser.__table__.c.id

        assert isinstance(column.type, Integer)
        assert column.primary_key is True
        assert column.index is True

    def test_created_at_column_configuration(self):
        """Test the created_at column configuration."""
        column = BaseTestUser.__table__.c.created_at

        assert isinstance(column.type, DateTime)
        assert column.nullable is False
        assert column.server_default is not None
        assert column.doc == "Timestamp when the record was created"

    def test_updated_at_column_configuration(self):
        """Test the updated_at column configuration."""
        column = BaseTestUser.__table__.c.updated_at

        assert isinstance(column.type, DateTime)
        assert column.nullable is False
        assert column.server_default is not None
        assert column.onupdate is not None
        assert column.doc == "Timestamp when the record was last updated"

    def test_tablename_is_generated_for_standard_class(self):
        """Test automatic table-name generation for a standard class."""
        assert BaseTestUser.__tablename__ == "base_test_users"

    def test_tablename_handles_acronym(self):
        """Test table-name generation handles acronyms."""
        assert BaseTestAPIKey.__tablename__ == "base_test_apikeys"

    def test_tablename_pluralizes_name_ending_in_s(self):
        """Test names ending in 's' receive 'es'."""
        assert BaseTestStatus.__tablename__ == "base_test_statuses"

    def test_tablename_pluralizes_name_ending_in_x(self):
        """Test names ending in 'x' receive 'es'."""
        assert BaseTestBox.__tablename__ == "base_test_boxes"

    def test_tablename_pluralizes_name_ending_in_ch(self):
        """Test names ending in 'ch' receive 'es'."""
        assert BaseTestBranch.__tablename__ == "base_test_branches"

    def test_tablename_pluralizes_name_ending_in_sh(self):
        """Test names ending in 'sh' receive 'es'."""
        assert BaseTestDish.__tablename__ == "base_test_dishes"

    def test_dict_returns_model_columns(self):
        """Test that dict returns all mapped model values."""
        user = BaseTestUser()

        user.id = 123
        user.created_at = datetime(2026, 9, 30, 12, 0, 0)
        user.updated_at = datetime(2026, 9, 30, 13, 0, 0)

        result = user.dict()

        assert result == {
            "id": 123,
            "created_at": datetime(2026, 9, 30, 12, 0, 0),
            "updated_at": datetime(2026, 9, 30, 13, 0, 0),
        }

    def test_dict_returns_none_for_unset_values(self):
        """Test that dict includes unset fields as None."""
        user = BaseTestUser()

        result = user.dict()

        assert result["id"] is None
        assert result["created_at"] is None
        assert result["updated_at"] is None

    def test_repr_with_id(self):
        """Test model string representation with an ID."""
        user = BaseTestUser()
        user.id = 42

        assert repr(user) == "<BaseTestUser(id=42)>"

    def test_repr_without_id(self):
        """Test model string representation before persistence."""
        user = BaseTestUser()

        assert repr(user) == "<BaseTestUser(id=None)>"

