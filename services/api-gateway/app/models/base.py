"""Base model class for SQLAlchemy ORM models.

This module provides the base class for all database models with common
fields and functionality shared across all tables.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, Integer, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all database models.

    Provides common columns and functionality:
    - id: Primary key (auto-incrementing integer)
    - created_at: Timestamp when record was created
    - updated_at: Timestamp when record was last updated

    Also provides automatic table name generation from class name.
    """

    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when the record was created",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when the record was last updated",
    )

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name.

        Converts CamelCase to snake_case and pluralizes.
        Example: User -> users, APIKey -> api_keys

        Returns:
            str: The generated table name.
        """
        # Convert CamelCase to snake_case
        name = cls.__name__
        # Handle acronyms like APIKey -> api_key
        import re
        name = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name).lower()
        # Pluralize (simple rule: add 's' or 'es')
        if name.endswith("s") or name.endswith("x") or name.endswith("ch") or name.endswith("sh"):
            name = name + "es"
        else:
            name = name + "s"
        return name

    def dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary.

        Returns:
            dict: Dictionary representation of the model.
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"