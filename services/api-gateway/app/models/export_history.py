"""Export History model for tracking user data exports.

This module defines the ExportHistory model for tracking
when users export data in various formats (CSV, PNG, PDF).
"""

from datetime import datetime
from typing import Optional, Dict, Any
import json

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Enum
from sqlalchemy.orm import relationship

from app.models.base import Base

import enum


class ExportStatus(str, enum.Enum):
    """Export job status.

    - PENDING: Export requested, waiting to start
    - PROCESSING: Export is being generated
    - COMPLETED: Export successfully generated
    - FAILED: Export generation failed
    - CANCELLED: Export was cancelled by user
    """

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportFormat(str, enum.Enum):
    """Export file formats.

    - CSV: Comma-separated values for data analysis
    - PNG: Image format for charts and graphs
    - PDF: Document format for reports
    - JSON: JSON format for API data
    - EXCEL: Excel format for spreadsheets
    """

    CSV = "csv"
    PNG = "png"
    PDF = "pdf"
    JSON = "json"
    EXCEL = "excel"


class ExportType(str, enum.Enum):
    """Export data types.

    - PREDICTIONS: BTC prediction data
    - ACCURACY: Prediction accuracy metrics
    - CORRELATIONS: BTC-macro correlation data
    - REGIMES: Market regime data
    - PRICES: Historical price data
    - INDICATORS: Macroeconomic indicators
    - RECOMMENDATIONS: Trade recommendations
    """

    PREDICTIONS = "predictions"
    ACCURACY = "accuracy"
    CORRELATIONS = "correlations"
    REGIMES = "regimes"
    PRICES = "prices"
    INDICATORS = "indicators"
    RECOMMENDATIONS = "recommendations"


class ExportHistory(Base):
    """Export History model for tracking user data exports.

    Attributes:
        user_id: Foreign key to the owning user
        export_type: Type of data exported
        format: File format of the export
        file_path: Path to the generated file (if stored)
        file_name: Original filename
        file_size: Size of the file in bytes
        parameters: JSON of export parameters
        status: Current status of the export job
        error_message: Error message if export failed
        expires_at: Optional expiration for temporary files
        download_count: Number of times the file was downloaded
        completed_at: Timestamp when export was completed
        user: Relationship to the owning User
    """

    __tablename__ = "export_histories"

    # Foreign key to user
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to the owning user",
    )

    # Export metadata
    export_type = Column(
        Enum(ExportType),
        nullable=False,
        doc="Type of data exported",
    )
    format = Column(
        Enum(ExportFormat),
        nullable=False,
        doc="File format of the export",
    )

    # File information
    file_path = Column(
        String(500),
        nullable=True,
        doc="Path to the generated file",
    )
    file_name = Column(
        String(255),
        nullable=True,
        doc="Original filename",
    )
    file_size = Column(
        Integer,
        nullable=True,
        doc="Size of the file in bytes",
    )

    # Export parameters
    parameters = Column(
        Text,
        nullable=True,
        doc="JSON of export parameters (timeframe, symbol, etc.)",
    )

    # Status and tracking
    status = Column(
        Enum(ExportStatus),
        default=ExportStatus.PENDING,
        nullable=False,
        doc="Current status of the export job",
    )
    error_message = Column(
        Text,
        nullable=True,
        doc="Error message if export failed",
    )

    # Expiration and usage
    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Expiration for temporary files",
    )
    download_count = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of times the file was downloaded",
    )

    # Timestamps
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when export was completed",
    )
    downloaded_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when file was last downloaded",
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="exports",
        doc="The user who requested this export",
    )

    def __repr__(self) -> str:
        """String representation of the export history entry."""
        return (
            f"<ExportHistory(id={self.id}, user_id={self.user_id}, "
            f"type='{self.export_type}', status='{self.status}')>"
        )

    @property
    def is_completed(self) -> bool:
        """Check if the export is completed.

        Returns:
            bool: True if status is COMPLETED.
        """
        return self.status == ExportStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if the export failed.

        Returns:
            bool: True if status is FAILED.
        """
        return self.status == ExportStatus.FAILED

    @property
    def is_pending(self) -> bool:
        """Check if the export is pending.

        Returns:
            bool: True if status is PENDING or PROCESSING.
        """
        return self.status in [ExportStatus.PENDING, ExportStatus.PROCESSING]

    @property
    def is_expired(self) -> bool:
        """Check if the export file has expired.

        Returns:
            bool: True if expires_at is in the past.
        """
        if self.expires_at is None:
            return False
        return datetime.now(datetime.now().astimezone().tzinfo) > self.expires_at

    @property
    def parameters_dict(self) -> Dict[str, Any]:
        """Get parameters as a dictionary.

        Returns:
            Dict[str, Any]: Parameters as a dictionary.
        """
        if not self.parameters:
            return {}
        try:
            return json.loads(self.parameters)
        except json.JSONDecodeError:
            return {}

    def set_parameters(self, params: Dict[str, Any]) -> None:
        """Set parameters from a dictionary.

        Args:
            params: Dictionary of parameters.
        """
        self.parameters = json.dumps(params)

    def mark_completed(self, file_path: str, file_name: str, file_size: int) -> None:
        """Mark the export as completed with file details.

        Args:
            file_path: Path to the generated file.
            file_name: Original filename.
            file_size: Size of the file in bytes.
        """
        self.status = ExportStatus.COMPLETED
        self.file_path = file_path
        self.file_name = file_name
        self.file_size = file_size
        self.completed_at = datetime.now(datetime.now().astimezone().tzinfo)

    def mark_failed(self, error_message: str) -> None:
        """Mark the export as failed with an error message.

        Args:
            error_message: Description of the error.
        """
        self.status = ExportStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now(datetime.now().astimezone().tzinfo)

    def mark_processing(self) -> None:
        """Mark the export as processing."""
        self.status = ExportStatus.PROCESSING

    def increment_download_count(self) -> None:
        """Increment the download count and update downloaded_at."""
        self.download_count += 1
        self.downloaded_at = datetime.now(datetime.now().astimezone().tzinfo)

    def set_expiry_days(self, days: int) -> None:
        """Set expiration date to a number of days from now.

        Args:
            days: Number of days until expiration.
        """
        from datetime import timedelta
        self.expires_at = datetime.now(datetime.now().astimezone().tzinfo) + timedelta(days=days)

    def dict(self) -> dict:
        """Convert export history to dictionary.

        Returns:
            dict: Export history data.
        """
        data = super().dict()
        # Add computed properties
        data["is_completed"] = self.is_completed
        data["is_failed"] = self.is_failed
        data["is_pending"] = self.is_pending
        data["is_expired"] = self.is_expired
        data["parameters"] = self.parameters_dict
        return data