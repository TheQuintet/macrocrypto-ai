# """Unit tests for ExportHistory model."""

# import pytest
# from datetime import datetime, timedelta, timezone

# from app.models.export_history import ExportHistory, ExportStatus, ExportType, ExportFormat


# class TestExportHistoryModel:
#     """Test ExportHistory model functionality."""

#     def test_create_export_history(self):
#         """Test creating an export history entry."""
#         export = ExportHistory(
#             user_id=1,
#             export_type=ExportType.PREDICTIONS,
#             format=ExportFormat.CSV
#         )
#         assert export.user_id == 1
#         assert export.export_type == ExportType.PREDICTIONS
#         assert export.format == ExportFormat.CSV
#         assert export.status == ExportStatus.PENDING
#         assert export.download_count == 0

#     def test_export_history_defaults(self):
#         """Test default values for ExportHistory."""
#         export = ExportHistory(
#             user_id=1,
#             export_type=ExportType.ACCURACY,
#             format=ExportFormat.PNG
#         )
#         assert export.status == ExportStatus.PENDING
#         assert export.download_count == 0
#         assert export.file_path is None
#         assert export.file_name is None
#         assert export.file_size is None
#         assert export.error_message is None

#     def test_export_status_properties(self):
#         """Test export status properties."""
#         export = ExportHistory(
#             user_id=1,
#             export_type=ExportType.PREDICTIONS,
#             format=ExportFormat.CSV
#         )

#         # Pending
#         assert export.is_pending is True
#         assert export.is_completed is False
#         assert export.is_failed is False

#         # Processing
#         export.status = ExportStatus.PROCESSING
#         assert export.is_pending is True
#         assert export.is_completed is False
#         assert export.is_failed is False

#         # Completed
#         export.status = ExportStatus.COMPLETED
#         assert export.is_pending is False
#         assert export.is_completed is True
#         assert export.is_failed is False

#         # Failed
#         export.status = ExportStatus.FAILED
#         assert export.is_pending is False
#         assert export.is_completed is False
#         assert export.is_failed is True

#     def test_export_mark_completed(self):
#         """Test marking export as completed."""
#         export = ExportHistory(
#             user_id=1,
#             export_type=ExportType.PREDICTIONS,
#             format=ExportFormat.CSV
#         )
#         export.mark_completed(
#             file_path="/exports/file.csv",
#             file_name="predictions.csv",
#             file_size=1024
#         )
#         assert export.status == ExportStatus.COMPLETED
#         assert export.file_path == "/exports/file.csv"
#         assert export.file_name == "predictions.csv"
#         assert export.file_size == 1024
#         assert export.completed_at is not None

#     def test_export_mark_failed(self):
#         """Test marking export as failed."""
#         export = ExportHistory(
#             user_id=1,
#             export_type=ExportType.PREDICTIONS,
#             format=ExportFormat.CSV
#         )
#         export.mark_failed("Database connection error")
#         assert export.status == ExportStatus.FAILED
#         assert export.error_message == "Database connection error"
#         assert export.completed_at is not None

#     def test_export_mark_processing(self):
#         """Test marking export as processing."""
#         export = ExportHistory(
#             user_id=1,
#             export_type=ExportType.PREDICTIONS,
#             format=ExportFormat.CSV
#         )
#         export.mark_processing()
#         assert export.status == ExportStatus.PROCESSING

#     def test_export_increment_download(self):
#         """Test incrementing download count."""
#         export = ExportHistory(
#             user_id=1,
#             export_type=ExportType.PREDICTIONS,
#             format=ExportFormat.CSV
#         )
#         assert export.download_count == 0
#         export.increment_download_count()
#         assert export.download_count == 1
#         assert export.downloaded_at is not None
#         export.increment_download_count()
#         assert export.download_count == 2

#     def test_export_expiration(self):
#         """Test export expiration properties."""
#         export = ExportHistory(
#             user_id=1,
#             export_type=ExportType.PREDICTIONS,
#             format=ExportFormat.CSV
#         )
#         assert export.is_expired is False

#         export.set_expiry_days(7)
#         assert export.expires_at is not None
#         diff = export.expires_at - datetime.now(timezone.utc)
#         assert 6 <= diff.days <= 8

#         # Set expiration in the past - use timezone-aware datetime
#         export.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
#         assert export.is_expired is True

#     def test_export_parameters(self):
#         """Test export parameters handling."""
#         export = ExportHistory(
#             user_id=1,
#             export_type=ExportType.PREDICTIONS,
#             format=ExportFormat.CSV
#         )
#         params = {"symbol": "BTC", "timeframe": "24h", "limit": 100}
#         export.set_parameters(params)
#         assert export.parameters_dict == params

#         # Test with invalid JSON
#         export.parameters = "invalid json"
#         assert export.parameters_dict == {}

#     def test_export_history_dict(self):
#         """Test dict() method includes computed properties."""
#         export = ExportHistory(
#             user_id=1,
#             export_type=ExportType.PREDICTIONS,
#             format=ExportFormat.CSV
#         )
#         export.set_parameters({"symbol": "BTC"})
#         data = export.dict()
#         assert "is_completed" in data
#         assert "is_failed" in data
#         assert "is_pending" in data
#         assert "is_expired" in data
#         assert data["parameters"] == {"symbol": "BTC"}