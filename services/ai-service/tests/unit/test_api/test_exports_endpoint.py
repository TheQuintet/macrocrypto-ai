"""Unit tests for the export download endpoint (A2.6).

Covers:
    - 200: a completed export with bytes in storage downloads
      successfully; the response carries the right content type
      and the exact bytes that were saved.
    - 404: missing row, row not completed (pending / failed),
      file missing from storage despite a completed row.
    - Download tracking: ``mark_downloaded`` is called on the row
      on success; its failure does not fail the request.
    - Both response shapes: FileResponse for LocalDiskStorage,
      plain Response for other backends.

The endpoint uses ``session_scope()`` directly and reads storage
via ``get_storage()``. Both are monkeypatched here so no database
connection is opened and no real files are written.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.database.repositories.export_history_repository import (
    ExportHistoryRow,
)
from app.export.storage import InMemoryStorage, LocalDiskStorage
from app.main import app


# ============================================================
# FAKE SESSION
# ============================================================
class _FakeSession:
    """A stand-in AsyncSession — the endpoint never touches it."""


@asynccontextmanager
async def _fake_session_scope():
    """Yield a fake session without opening a database connection."""
    yield _FakeSession()


# ============================================================
# FAKE HISTORY REPOSITORY
# ============================================================
class _FakeHistoryRepo:
    """Records mark_downloaded calls; serves canned rows."""

    rows: List[Dict[str, Any]] = []
    mark_downloaded_calls: List[int] = []
    mark_downloaded_raises: Optional[BaseException] = None

    def __init__(self, session: Any) -> None:
        self.session = session

    async def fetch_history(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        timeframe: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        return [dict(r) for r in _FakeHistoryRepo.rows]

    async def mark_downloaded(self, export_id: int) -> int:
        _FakeHistoryRepo.mark_downloaded_calls.append(export_id)
        if _FakeHistoryRepo.mark_downloaded_raises is not None:
            raise _FakeHistoryRepo.mark_downloaded_raises
        return 1


# ============================================================
# FIXTURES
# ============================================================
@pytest.fixture(autouse=True)
def _patch_endpoint(monkeypatch):
    """Patch the endpoint's collaborators on every test."""
    import app.api.v1.download as dl

    monkeypatch.setattr(dl, "session_scope", _fake_session_scope)
    monkeypatch.setattr(dl, "ExportHistoryRepository", _FakeHistoryRepo)

    # Reset shared state.
    _FakeHistoryRepo.rows = []
    _FakeHistoryRepo.mark_downloaded_calls = []
    _FakeHistoryRepo.mark_downloaded_raises = None

    yield


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def _completed_row(
    *,
    export_id: int = 1,
    file_name: str = "macro-crypto-btc_price-30d-2026-09-16.csv",
    export_type: str = "csv",
) -> Dict[str, Any]:
    return {
        "id": export_id,
        "user_id": "analyst-42",
        "export_type": export_type,
        "data_types": ["btc_price"],
        "timeframe": "30d",
        "file_name": file_name,
        "file_size": 10,
        "status": "completed",
        "created_at": datetime(2026, 9, 16, tzinfo=timezone.utc),
        "downloaded_at": None,
    }


# ============================================================
# 200 — HAPPY PATH
# ============================================================
class TestDownloadHappyPath:
    """A completed export with bytes on disk downloads."""

    def test_csv_download(self, client: TestClient) -> None:
        storage = InMemoryStorage()
        payload = b"data_type,time,close\nbtc_price,2026-09-14T00:00:00+00:00,60000.0\n"
        storage.save("macro-crypto-btc_price-30d-2026-09-16.csv", payload)

        _FakeHistoryRepo.rows = [_completed_row(export_type="csv")]

        with patch(
            "app.api.v1.download.get_storage", return_value=storage
        ):
            response = client.get(
                "/api/v1/exports/macro-crypto-btc_price-30d-2026-09-16.csv"
            )

        assert response.status_code == 200
        assert response.content == payload
        assert response.headers["content-type"].startswith("text/csv")

    def test_png_download_content_type(self, client: TestClient) -> None:
        storage = InMemoryStorage()
        storage.save(
            "macro-crypto-chart-30d-2026-09-16.png",
            b"\x89PNG\r\n\x1a\nfake",
        )
        _FakeHistoryRepo.rows = [
            _completed_row(
                file_name="macro-crypto-chart-30d-2026-09-16.png",
                export_type="png",
            )
        ]

        with patch(
            "app.api.v1.download.get_storage", return_value=storage
        ):
            response = client.get(
                "/api/v1/exports/macro-crypto-chart-30d-2026-09-16.png"
            )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/png")

    def test_pdf_download_content_type(self, client: TestClient) -> None:
        storage = InMemoryStorage()
        storage.save(
            "macro-crypto-report-30d-2026-09-16.pdf",
            b"%PDF-1.4\nfake",
        )
        _FakeHistoryRepo.rows = [
            _completed_row(
                file_name="macro-crypto-report-30d-2026-09-16.pdf",
                export_type="pdf",
            )
        ]

        with patch(
            "app.api.v1.download.get_storage", return_value=storage
        ):
            response = client.get(
                "/api/v1/exports/macro-crypto-report-30d-2026-09-16.pdf"
            )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith(
            "application/pdf"
        )

    def test_file_response_for_local_disk(
        self, client: TestClient, tmp_path
    ) -> None:
        """LocalDiskStorage path produces a streaming FileResponse."""
        storage = LocalDiskStorage(tmp_path)
        payload = b"streamed bytes"
        storage.save("macro-crypto-btc_price-30d-2026-09-16.csv", payload)
        _FakeHistoryRepo.rows = [_completed_row(export_type="csv")]

        with patch(
            "app.api.v1.download.get_storage", return_value=storage
        ):
            response = client.get(
                "/api/v1/exports/macro-crypto-btc_price-30d-2026-09-16.csv"
            )

        assert response.status_code == 200
        assert response.content == payload


# ============================================================
# DOWNLOAD TRACKING
# ============================================================
class TestDownloadTracking:
    """mark_downloaded is called on success, best-effort."""

    def test_mark_downloaded_is_called(
        self, client: TestClient
    ) -> None:
        storage = InMemoryStorage()
        storage.save("f.csv", b"x")
        _FakeHistoryRepo.rows = [
            _completed_row(export_id=42, file_name="f.csv", export_type="csv")
        ]

        with patch(
            "app.api.v1.download.get_storage", return_value=storage
        ):
            response = client.get("/api/v1/exports/f.csv")

        assert response.status_code == 200
        assert _FakeHistoryRepo.mark_downloaded_calls == [42]

    def test_mark_downloaded_failure_does_not_fail_request(
        self, client: TestClient
    ) -> None:
        storage = InMemoryStorage()
        storage.save("f.csv", b"x")
        _FakeHistoryRepo.rows = [
            _completed_row(export_id=42, file_name="f.csv")
        ]
        _FakeHistoryRepo.mark_downloaded_raises = RuntimeError("db down")

        with patch(
            "app.api.v1.download.get_storage", return_value=storage
        ):
            response = client.get("/api/v1/exports/f.csv")

        assert response.status_code == 200
        assert response.content == b"x"


# ============================================================
# 404 — MISSING / NOT READY
# ============================================================
class TestDownloadMissing:
    """404 for every reason the export is not downloadable."""

    def test_no_rows_returns_404(self, client: TestClient) -> None:
        _FakeHistoryRepo.rows = []
        with patch(
            "app.api.v1.download.get_storage",
            return_value=InMemoryStorage(),
        ):
            response = client.get("/api/v1/exports/does-not-exist.csv")
        assert response.status_code == 404

    def test_row_with_different_name_returns_404(
        self, client: TestClient
    ) -> None:
        _FakeHistoryRepo.rows = [
            _completed_row(file_name="other.csv")
        ]
        with patch(
            "app.api.v1.download.get_storage",
            return_value=InMemoryStorage(),
        ):
            response = client.get("/api/v1/exports/f.csv")
        assert response.status_code == 404

    def test_pending_row_returns_404(self, client: TestClient) -> None:
        row = _completed_row()
        row["status"] = "pending"
        _FakeHistoryRepo.rows = [row]
        storage = InMemoryStorage()
        storage.save("macro-crypto-btc_price-30d-2026-09-16.csv", b"x")

        with patch(
            "app.api.v1.download.get_storage", return_value=storage
        ):
            response = client.get(
                "/api/v1/exports/macro-crypto-btc_price-30d-2026-09-16.csv"
            )
        assert response.status_code == 404

    def test_failed_row_returns_404(self, client: TestClient) -> None:
        row = _completed_row()
        row["status"] = "failed"
        _FakeHistoryRepo.rows = [row]
        storage = InMemoryStorage()
        storage.save("macro-crypto-btc_price-30d-2026-09-16.csv", b"x")

        with patch(
            "app.api.v1.download.get_storage", return_value=storage
        ):
            response = client.get(
                "/api/v1/exports/macro-crypto-btc_price-30d-2026-09-16.csv"
            )
        assert response.status_code == 404

    def test_completed_row_but_no_file_returns_404(
        self, client: TestClient
    ) -> None:
        """Row says completed but the file has been swept."""
        _FakeHistoryRepo.rows = [_completed_row()]
        empty_storage = InMemoryStorage()

        with patch(
            "app.api.v1.download.get_storage",
            return_value=empty_storage,
        ):
            response = client.get(
                "/api/v1/exports/macro-crypto-btc_price-30d-2026-09-16.csv"
            )
        assert response.status_code == 404
        # And we did not record a download for a file that was not
        # served.
        assert _FakeHistoryRepo.mark_downloaded_calls == []


# ============================================================
# ROUTE SHAPE
# ============================================================
class TestRouteShape:
    """The route is registered at the expected path."""

    def test_endpoint_path_is_prefixed(self) -> None:
        from app.api.v1.download import router

        assert router.prefix == "/api/v1/exports"
        paths = [r.path for r in router.routes]
        assert "/api/v1/exports/{file_name}" in paths