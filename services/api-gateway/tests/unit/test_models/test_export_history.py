"""Tests for the ExportHistory model."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import DateTime, Enum, Integer, String, Text

from app.models.export_history import (
    ExportFormat,
    ExportHistory,
    ExportStatus,
    ExportType,
)


class TestExportEnums:
    """Test export-related enumerations."""

    def test_export_status_values(self):
        """Test all export status values."""
        assert ExportStatus.PENDING.value == "pending"
        assert ExportStatus.PROCESSING.value == "processing"
        assert ExportStatus.COMPLETED.value == "completed"
        assert ExportStatus.FAILED.value == "failed"
        assert ExportStatus.CANCELLED.value == "cancelled"

    def test_export_format_values(self):
        """Test all export format values."""
        assert ExportFormat.CSV.value == "csv"
        assert ExportFormat.PNG.value == "png"
        assert ExportFormat.PDF.value == "pdf"
        assert ExportFormat.JSON.value == "json"
        assert ExportFormat.EXCEL.value == "excel"

    def test_export_type_values(self):
        """Test all export type values."""
        assert ExportType.PREDICTIONS.value == "predictions"
        assert ExportType.ACCURACY.value == "accuracy"
        assert ExportType.CORRELATIONS.value == "correlations"
        assert ExportType.REGIMES.value == "regimes"
        assert ExportType.PRICES.value == "prices"
        assert ExportType.INDICATORS.value == "indicators"
        assert ExportType.RECOMMENDATIONS.value == "recommendations"


class TestExportHistoryModel:
    """Test ExportHistory model configuration and behavior."""

    def test_table_name(self):
        """Test the explicitly configured table name."""
        assert ExportHistory.__tablename__ == "export_histories"

    def test_required_columns_exist(self):
        """Test that expected model columns exist."""
        columns = ExportHistory.__table__.c

        expected_columns = {
            "id",
            "created_at",
            "updated_at",
            "user_id",
            "export_type",
            "format",
            "file_path",
            "file_name",
            "file_size",
            "parameters",
            "status",
            "error_message",
            "expires_at",
            "download_count",
            "completed_at",
            "downloaded_at",
        }

        assert expected_columns.issubset(set(columns.keys()))

    def test_user_id_column_configuration(self):
        """Test user foreign-key column configuration."""
        column = ExportHistory.__table__.c.user_id

        assert isinstance(column.type, Integer)
        assert column.nullable is False
        assert column.index is True
        assert len(column.foreign_keys) == 1

        foreign_key = next(iter(column.foreign_keys))
        assert str(foreign_key.target_fullname) == "users.id"

    def test_export_metadata_columns(self):
        """Test export type and format columns."""
        export_type = ExportHistory.__table__.c.export_type
        export_format = ExportHistory.__table__.c.format

        assert isinstance(export_type.type, Enum)
        assert isinstance(export_format.type, Enum)
        assert export_type.nullable is False
        assert export_format.nullable is False

    def test_file_columns_configuration(self):
        """Test file-related column configuration."""
        file_path = ExportHistory.__table__.c.file_path
        file_name = ExportHistory.__table__.c.file_name
        file_size = ExportHistory.__table__.c.file_size

        assert isinstance(file_path.type, String)
        assert file_path.type.length == 500
        assert file_path.nullable is True

        assert isinstance(file_name.type, String)
        assert file_name.type.length == 255
        assert file_name.nullable is True

        assert isinstance(file_size.type, Integer)
        assert file_size.nullable is True

    def test_parameters_column_configuration(self):
        """Test export parameters column configuration."""
        column = ExportHistory.__table__.c.parameters

        assert isinstance(column.type, Text)
        assert column.nullable is True

    def test_status_column_configuration(self):
        """Test status column configuration."""
        column = ExportHistory.__table__.c.status

        assert isinstance(column.type, Enum)
        assert column.nullable is False
        assert column.default is not None

    def test_tracking_columns_configuration(self):
        """Test export tracking columns."""
        columns = ExportHistory.__table__.c

        assert isinstance(columns.error_message.type, Text)
        assert isinstance(columns.expires_at.type, DateTime)
        assert isinstance(columns.download_count.type, Integer)
        assert isinstance(columns.completed_at.type, DateTime)
        assert isinstance(columns.downloaded_at.type, DateTime)

        assert columns.error_message.nullable is True
        assert columns.expires_at.nullable is True
        assert columns.download_count.nullable is False
        assert columns.completed_at.nullable is True
        assert columns.downloaded_at.nullable is True

    def test_default_values(self):
        """Test model defaults assigned by __init__."""
        export = ExportHistory()

        assert export.status == ExportStatus.PENDING
        assert export.download_count == 0

    def test_explicit_values_are_preserved(self):
        """Test explicitly supplied status and download count."""
        export = ExportHistory(
            status=ExportStatus.PROCESSING,
            download_count=5,
        )

        assert export.status == ExportStatus.PROCESSING
        assert export.download_count == 5

    def test_none_values_receive_defaults(self):
        """Test None values are replaced by model defaults."""
        export = ExportHistory(
            status=None,
            download_count=None,
        )

        assert export.status == ExportStatus.PENDING
        assert export.download_count == 0

    def test_repr(self):
        """Test string representation."""
        export = ExportHistory(
            user_id=42,
            export_type=ExportType.PREDICTIONS,
            status=ExportStatus.COMPLETED,
        )
        export.id = 10

        result = repr(export)

        assert result == (
            "<ExportHistory(id=10, user_id=42, "
            "type='ExportType.PREDICTIONS', status='ExportStatus.COMPLETED')>"
        )


class TestExportHistoryProperties:
    """Test computed ExportHistory properties."""

    def test_is_completed(self):
        """Test completed status detection."""
        export = ExportHistory(status=ExportStatus.COMPLETED)

        assert export.is_completed is True
        assert export.is_failed is False
        assert export.is_pending is False

    def test_is_failed(self):
        """Test failed status detection."""
        export = ExportHistory(status=ExportStatus.FAILED)

        assert export.is_completed is False
        assert export.is_failed is True
        assert export.is_pending is False

    def test_is_pending_for_pending_status(self):
        """Test pending status detection."""
        export = ExportHistory(status=ExportStatus.PENDING)

        assert export.is_pending is True
        assert export.is_completed is False
        assert export.is_failed is False

    def test_is_pending_for_processing_status(self):
        """Test processing is considered pending."""
        export = ExportHistory(status=ExportStatus.PROCESSING)

        assert export.is_pending is True
        assert export.is_completed is False
        assert export.is_failed is False

    def test_cancelled_is_not_pending(self):
        """Test cancelled exports are not considered pending."""
        export = ExportHistory(status=ExportStatus.CANCELLED)

        assert export.is_pending is False
        assert export.is_completed is False
        assert export.is_failed is False

    def test_is_expired_without_expiry(self):
        """Test exports without an expiry date are not expired."""
        export = ExportHistory()

        assert export.expires_at is None
        assert export.is_expired is False

    def test_is_expired_when_expiry_is_in_the_past(self):
        """Test expired exports."""
        export = ExportHistory(
            expires_at=datetime.now(timezone.utc) - timedelta(days=1)
        )

        assert export.is_expired is True

    def test_is_expired_when_expiry_is_in_the_future(self):
        """Test exports that have not expired."""
        export = ExportHistory(
            expires_at=datetime.now(timezone.utc) + timedelta(days=1)
        )

        assert export.is_expired is False


class TestExportHistoryParameters:
    """Test export parameter serialization."""

    def test_parameters_dict_without_parameters(self):
        """Test empty parameters return an empty dictionary."""
        export = ExportHistory()

        assert export.parameters is None
        assert export.parameters_dict == {}

    def test_parameters_dict_with_valid_json(self):
        """Test valid JSON parameters are decoded."""
        export = ExportHistory()
        export.parameters = '{"symbol": "BTC", "days": 30}'

        assert export.parameters_dict == {
            "symbol": "BTC",
            "days": 30,
        }

    def test_parameters_dict_with_invalid_json(self):
        """Test invalid JSON returns an empty dictionary."""
        export = ExportHistory()
        export.parameters = "not valid json"

        assert export.parameters_dict == {}

    def test_set_parameters(self):
        """Test dictionary parameters are serialized as JSON."""
        export = ExportHistory()

        params = {
            "symbol": "BTC",
            "days": 30,
            "include_macro": True,
        }

        export.set_parameters(params)

        assert export.parameters_dict == params

    def test_set_parameters_produces_json_string(self):
        """Test set_parameters stores JSON text."""
        export = ExportHistory()

        export.set_parameters({"symbol": "BTC"})

        assert isinstance(export.parameters, str)


class TestExportHistoryStateChanges:
    """Test export status and lifecycle methods."""

    def test_mark_completed(self):
        """Test marking an export as completed."""
        export = ExportHistory()

        before = datetime.now(timezone.utc)
        export.mark_completed(
            file_path="/exports/btc.csv",
            file_name="btc.csv",
            file_size=1024,
        )
        after = datetime.now(timezone.utc)

        assert export.status == ExportStatus.COMPLETED
        assert export.file_path == "/exports/btc.csv"
        assert export.file_name == "btc.csv"
        assert export.file_size == 1024
        assert export.completed_at is not None
        assert before <= export.completed_at <= after
        assert export.is_completed is True

    def test_mark_failed(self):
        """Test marking an export as failed."""
        export = ExportHistory()

        before = datetime.now(timezone.utc)
        export.mark_failed("Export generation failed")
        after = datetime.now(timezone.utc)

        assert export.status == ExportStatus.FAILED
        assert export.error_message == "Export generation failed"
        assert export.completed_at is not None
        assert before <= export.completed_at <= after
        assert export.is_failed is True

    def test_mark_processing(self):
        """Test marking an export as processing."""
        export = ExportHistory()

        export.mark_processing()

        assert export.status == ExportStatus.PROCESSING
        assert export.is_pending is True

    def test_increment_download_count(self):
        """Test download count is incremented."""
        export = ExportHistory()

        before = datetime.now(timezone.utc)
        export.increment_download_count()
        after = datetime.now(timezone.utc)

        assert export.download_count == 1
        assert export.downloaded_at is not None
        assert before <= export.downloaded_at <= after

    def test_increment_download_count_multiple_times(self):
        """Test multiple downloads are counted."""
        export = ExportHistory()

        export.increment_download_count()
        export.increment_download_count()
        export.increment_download_count()

        assert export.download_count == 3
        assert export.downloaded_at is not None

    def test_set_expiry_days(self):
        """Test expiry is calculated from the current time."""
        export = ExportHistory()

        before = datetime.now(timezone.utc)
        export.set_expiry_days(7)
        after = datetime.now(timezone.utc)

        assert export.expires_at is not None

        expected_before = before + timedelta(days=7)
        expected_after = after + timedelta(days=7)

        assert expected_before <= export.expires_at <= expected_after


class TestExportHistoryDict:
    """Test dictionary serialization."""

    def test_dict_contains_base_and_export_fields(self):
        """Test dict contains mapped model fields and computed properties."""
        export = ExportHistory(
            user_id=42,
            export_type=ExportType.PREDICTIONS,
            format=ExportFormat.CSV,
            status=ExportStatus.COMPLETED,
            download_count=2,
        )
        export.id = 10
        export.parameters = '{"symbol": "BTC"}'

        result = export.dict()

        assert result["id"] == 10
        assert result["user_id"] == 42
        assert result["export_type"] == ExportType.PREDICTIONS
        assert result["format"] == ExportFormat.CSV
        assert result["status"] == ExportStatus.COMPLETED
        assert result["download_count"] == 2
        assert result["is_completed"] is True
        assert result["is_failed"] is False
        assert result["is_pending"] is False
        assert result["is_expired"] is False
        assert result["parameters"] == {"symbol": "BTC"}

    def test_dict_with_failed_export(self):
        """Test computed properties for a failed export."""
        export = ExportHistory(status=ExportStatus.FAILED)
        export.parameters = '{"reason": "timeout"}'

        result = export.dict()

        assert result["is_completed"] is False
        assert result["is_failed"] is True
        assert result["is_pending"] is False
        assert result["parameters"] == {"reason": "timeout"}

    def test_dict_with_pending_export(self):
        """Test computed properties for a pending export."""
        export = ExportHistory()

        result = export.dict()

        assert result["is_completed"] is False
        assert result["is_failed"] is False
        assert result["is_pending"] is True
        assert result["parameters"] == {}

