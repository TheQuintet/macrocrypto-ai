"""Unit tests for app.export.service.

Covers:
    - generate_csv_export: happy path (pending → completed)
    - generate_csv_export: failure path (mark_failed + re-raise)
    - generate_png_export: happy path (pending → completed)
    - generate_png_export: failure path (mark_failed + re-raise)
    - The exact filename and file_size passed to mark_completed
    - That mark_failed is NOT allowed to mask the original error
    - That generate_png_export records export_type='png' and
      data_types=['chart'] on the history row

The service owns ``session_scope()`` and constructs its own
repositories, so the test monkeypatches five things on
``app.export.service``:

    - session_scope: an asynccontextmanager yielding a fake session
    - ExportHistoryRepository: a recording fake
    - PredictionRepository / CorrelationRepository: no-op fakes
    - CsvExporter: a fake that either returns a canned result or
      raises a canned exception
    - PngExporter: a fake with the same contract, but a
      ``render`` method and a single-argument ``_filename``

Note on ``_FakeExporter._filename`` / ``_FakePngExporter._filename``:

    Both service functions call ``<Exporter>._filename(...)`` to
    compute a provisional name *before* the session opens, so the
    fakes must expose that static method. The service tests do not
    care what the name looks like — the naming conventions are
    covered exhaustively in ``test_csv_export.py`` and
    ``test_png_export.py``. The fakes return fixed placeholders,
    which the happy-path tests assert are passed through to
    ``create_request`` unchanged.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pytest

from app.export.csv_export import ExportRequest, ExportResult
from app.export.png_export import ChartRequest, ChartResult
from app.export.service import (
    generate_csv_export,
    generate_png_export,
)


# ============================================================
# FAKE SESSION
# ============================================================
class _FakeSession:
    """A stand-in AsyncSession — the service never touches it directly."""


@asynccontextmanager
async def _fake_session_scope():
    """Yield a fake session without opening a database connection."""
    yield _FakeSession()


# ============================================================
# FAKE HISTORY REPOSITORY
# ============================================================
class _FakeHistoryRepo:
    """Records create_request / mark_completed / mark_failed calls."""

    # Class-level switch so individual tests can pick the id
    # the fake returns from create_request.
    next_id: int = 1
    # Set to an exception type to make mark_failed raise.
    mark_failed_raises: Optional[BaseException] = None

    instances: List["_FakeHistoryRepo"] = []

    def __init__(self, session: Any) -> None:
        self.session = session
        self.created: List[Any] = []
        self.completed: List[Dict[str, Any]] = []
        self.failed: List[int] = []
        _FakeHistoryRepo.instances.append(self)

    async def create_request(self, row: Any) -> int:
        self.created.append(row)
        return _FakeHistoryRepo.next_id

    async def mark_completed(
        self,
        export_id: int,
        file_name: str,
        file_size: int,
    ) -> int:
        self.completed.append(
            {
                "export_id": export_id,
                "file_name": file_name,
                "file_size": file_size,
            }
        )
        return 1

    async def mark_failed(self, export_id: int) -> int:
        self.failed.append(export_id)
        if _FakeHistoryRepo.mark_failed_raises is not None:
            raise _FakeHistoryRepo.mark_failed_raises
        return 1


# ============================================================
# FAKE PREDICTION / CORRELATION REPOS
# ============================================================
class _NoopRepo:
    """Accepts a session and does nothing."""

    def __init__(self, session: Any) -> None:
        self.session = session


# ============================================================
# FAKE CSV EXPORTER
# ============================================================
class _FakeExporter:
    """Returns a canned ExportResult or raises a canned exception.

    Mirrors the two attributes of the real ``CsvExporter`` that
    ``generate_csv_export`` touches: the ``_filename`` static
    method (called before the session opens) and an instance
    ``build`` method (called inside the session).
    """

    # Class-level canned outcome, set per test.
    result: Optional[ExportResult] = None
    raises: Optional[BaseException] = None
    last_request: Optional[ExportRequest] = None

    # Fixed placeholder returned by the fake's ``_filename``. The
    # real naming convention is covered in test_csv_export.py; the
    # service test only asserts this string reaches create_request.
    PLACEHOLDER_NAME = "provisional.csv"

    def __init__(self, prediction_repo: Any, correlation_repo: Any) -> None:
        self.prediction_repo = prediction_repo
        self.correlation_repo = correlation_repo

    @staticmethod
    def _filename(data_types: List[str], timeframe: str) -> str:
        return _FakeExporter.PLACEHOLDER_NAME

    async def build(self, request: ExportRequest) -> ExportResult:
        _FakeExporter.last_request = request
        if _FakeExporter.raises is not None:
            raise _FakeExporter.raises
        assert _FakeExporter.result is not None
        return _FakeExporter.result


# ============================================================
# FAKE PNG EXPORTER
# ============================================================
class _FakePngExporter:
    """Returns a canned ChartResult or raises a canned exception.

    Mirrors the two attributes of the real ``PngExporter`` that
    ``generate_png_export`` touches: the ``_filename`` static
    method (called before the session opens) and an instance
    ``render`` method (called inside the session).
    """

    # Class-level canned outcome, set per test.
    result: Optional[ChartResult] = None
    raises: Optional[BaseException] = None
    last_request: Optional[ChartRequest] = None

    # Fixed placeholder returned by the fake's ``_filename``. The
    # real naming convention is covered in test_png_export.py.
    PLACEHOLDER_NAME = "provisional.png"

    def __init__(self, prediction_repo: Any) -> None:
        self.prediction_repo = prediction_repo

    @staticmethod
    def _filename(timeframe: str) -> str:
        return _FakePngExporter.PLACEHOLDER_NAME

    async def render(self, request: ChartRequest) -> ChartResult:
        _FakePngExporter.last_request = request
        if _FakePngExporter.raises is not None:
            raise _FakePngExporter.raises
        assert _FakePngExporter.result is not None
        return _FakePngExporter.result


# ============================================================
# FIXTURES
# ============================================================
@pytest.fixture(autouse=True)
def _patch_service(monkeypatch):
    """Patch the collaborators the service imports by name."""
    import app.export.service as svc

    monkeypatch.setattr(svc, "session_scope", _fake_session_scope)
    monkeypatch.setattr(
        svc, "ExportHistoryRepository", _FakeHistoryRepo
    )
    monkeypatch.setattr(svc, "PredictionRepository", _NoopRepo)
    monkeypatch.setattr(svc, "CorrelationRepository", _NoopRepo)
    monkeypatch.setattr(svc, "CsvExporter", _FakeExporter)
    monkeypatch.setattr(svc, "PngExporter", _FakePngExporter)

    # Reset shared state.
    _FakeHistoryRepo.next_id = 1
    _FakeHistoryRepo.mark_failed_raises = None
    _FakeHistoryRepo.instances = []
    _FakeExporter.result = None
    _FakeExporter.raises = None
    _FakeExporter.last_request = None
    _FakePngExporter.result = None
    _FakePngExporter.raises = None
    _FakePngExporter.last_request = None

    yield


def _canned_result(file_name: str = "out.csv") -> ExportResult:
    return ExportResult(
        file_name=file_name,
        file_size=1234,
        data_types=["btc_price"],
        timeframe="30d",
        rows_written=10,
        content=b"a,b\n1,2\n",
    )


def _canned_png_result(file_name: str = "out.png") -> ChartResult:
    return ChartResult(
        file_name=file_name,
        file_size=2048,
        timeframe="30d",
        rows_plotted=42,
        content=b"\x89PNG\r\n\x1a\nfake",
    )


# ============================================================
# CSV — HAPPY PATH
# ============================================================
class TestGenerateCsvExportHappyPath:
    """generate_csv_export: pending → completed."""

    @pytest.mark.asyncio
    async def test_returns_exporter_result(self) -> None:
        _FakeExporter.result = _canned_result()
        req = ExportRequest(
            data_types=["btc_price"], timeframe="30d", user_id="u-1"
        )
        result = await generate_csv_export(req)
        assert result.file_name == "out.csv"
        assert result.file_size == 1234
        assert result.rows_written == 10

    @pytest.mark.asyncio
    async def test_inserts_pending_row_first(self) -> None:
        _FakeExporter.result = _canned_result()
        req = ExportRequest(
            data_types=["btc_price"], timeframe="30d", user_id="u-1"
        )
        await generate_csv_export(req)

        repo = _FakeHistoryRepo.instances[0]
        assert len(repo.created) == 1
        pending = repo.created[0]
        assert pending.export_type == "csv"
        assert pending.timeframe == "30d"
        assert pending.status == "pending"
        assert pending.user_id == "u-1"
        assert pending.data_types == ["btc_price"]
        # The provisional name must be a string. The real naming
        # convention is asserted in test_csv_export.py; here we
        # only pin that a non-empty value reached the NOT NULL
        # column.
        assert pending.file_name == _FakeExporter.PLACEHOLDER_NAME

    @pytest.mark.asyncio
    async def test_marks_completed_with_real_name_and_size(self) -> None:
        _FakeExporter.result = _canned_result(
            file_name="macro-crypto-btc_price-30d-2026-09-16.csv"
        )
        req = ExportRequest(data_types=["btc_price"], timeframe="30d")
        await generate_csv_export(req)

        repo = _FakeHistoryRepo.instances[0]
        assert len(repo.completed) == 1
        completed = repo.completed[0]
        assert completed["export_id"] == 1
        assert (
            completed["file_name"]
            == "macro-crypto-btc_price-30d-2026-09-16.csv"
        )
        assert completed["file_size"] == 1234

    @pytest.mark.asyncio
    async def test_passes_the_request_through_to_the_exporter(self) -> None:
        _FakeExporter.result = _canned_result()
        req = ExportRequest(
            data_types=["macro", "correlations"],
            timeframe="1y",
            user_id="analyst-9",
        )
        await generate_csv_export(req)
        assert _FakeExporter.last_request is req

    @pytest.mark.asyncio
    async def test_does_not_mark_failed_on_success(self) -> None:
        _FakeExporter.result = _canned_result()
        req = ExportRequest(data_types=["btc_price"], timeframe="30d")
        await generate_csv_export(req)
        repo = _FakeHistoryRepo.instances[0]
        assert repo.failed == []

    @pytest.mark.asyncio
    async def test_user_id_none_is_recorded_as_none(self) -> None:
        _FakeExporter.result = _canned_result()
        req = ExportRequest(data_types=["btc_price"], timeframe="30d")
        await generate_csv_export(req)
        repo = _FakeHistoryRepo.instances[0]
        assert repo.created[0].user_id is None


# ============================================================
# CSV — FAILURE PATH
# ============================================================
class TestGenerateCsvExportFailurePath:
    """generate_csv_export: exporter raises → mark_failed + re-raise."""

    @pytest.mark.asyncio
    async def test_re_raises_the_original_exception(self) -> None:
        _FakeExporter.raises = ValueError("boom")
        req = ExportRequest(data_types=["btc_price"], timeframe="30d")
        with pytest.raises(ValueError, match="boom"):
            await generate_csv_export(req)

    @pytest.mark.asyncio
    async def test_marks_failed(self) -> None:
        _FakeExporter.raises = ValueError("boom")
        req = ExportRequest(data_types=["btc_price"], timeframe="30d")
        with pytest.raises(ValueError):
            await generate_csv_export(req)

        repo = _FakeHistoryRepo.instances[0]
        assert repo.failed == [1]

    @pytest.mark.asyncio
    async def test_does_not_mark_completed(self) -> None:
        _FakeExporter.raises = ValueError("boom")
        req = ExportRequest(data_types=["btc_price"], timeframe="30d")
        with pytest.raises(ValueError):
            await generate_csv_export(req)

        repo = _FakeHistoryRepo.instances[0]
        assert repo.completed == []

    @pytest.mark.asyncio
    async def test_mark_failed_does_not_mask_the_original_error(self) -> None:
        _FakeExporter.raises = ValueError("original error")
        _FakeHistoryRepo.mark_failed_raises = RuntimeError("cleanup boom")

        req = ExportRequest(data_types=["btc_price"], timeframe="30d")
        with pytest.raises(ValueError, match="original error"):
            await generate_csv_export(req)

    @pytest.mark.asyncio
    async def test_mark_failed_is_still_attempted(self) -> None:
        _FakeExporter.raises = ValueError("original error")
        _FakeHistoryRepo.mark_failed_raises = RuntimeError("cleanup boom")

        req = ExportRequest(data_types=["btc_price"], timeframe="30d")
        with pytest.raises(ValueError):
            await generate_csv_export(req)

        repo = _FakeHistoryRepo.instances[0]
        # The mark_failed call was attempted (and raised) — the
        # fake records the id before raising.
        assert repo.failed == [1]


# ============================================================
# PNG — HAPPY PATH
# ============================================================
class TestGeneratePngExportHappyPath:
    """generate_png_export: pending → completed."""

    @pytest.mark.asyncio
    async def test_returns_exporter_result(self) -> None:
        _FakePngExporter.result = _canned_png_result()
        req = ChartRequest(timeframe="30d", user_id="u-1")
        result = await generate_png_export(req)
        assert result.file_name == "out.png"
        assert result.file_size == 2048
        assert result.rows_plotted == 42

    @pytest.mark.asyncio
    async def test_inserts_pending_row_first(self) -> None:
        _FakePngExporter.result = _canned_png_result()
        req = ChartRequest(timeframe="30d", user_id="u-1")
        await generate_png_export(req)

        repo = _FakeHistoryRepo.instances[0]
        assert len(repo.created) == 1
        pending = repo.created[0]
        assert pending.export_type == "png"
        assert pending.timeframe == "30d"
        assert pending.status == "pending"
        assert pending.user_id == "u-1"
        # The data_types column carries the storage-level 'chart'
        # label added to VALID_DATA_TYPE_NAMES for A2.3. It is not
        # a stream a CSV exporter produces.
        assert pending.data_types == ["chart"]
        assert pending.file_name == _FakePngExporter.PLACEHOLDER_NAME

    @pytest.mark.asyncio
    async def test_marks_completed_with_real_name_and_size(self) -> None:
        _FakePngExporter.result = _canned_png_result(
            file_name="macro-crypto-chart-30d-2026-09-16.png"
        )
        req = ChartRequest(timeframe="30d")
        await generate_png_export(req)

        repo = _FakeHistoryRepo.instances[0]
        assert len(repo.completed) == 1
        completed = repo.completed[0]
        assert completed["export_id"] == 1
        assert (
            completed["file_name"]
            == "macro-crypto-chart-30d-2026-09-16.png"
        )
        assert completed["file_size"] == 2048

    @pytest.mark.asyncio
    async def test_passes_the_request_through_to_the_exporter(self) -> None:
        _FakePngExporter.result = _canned_png_result()
        req = ChartRequest(
            timeframe="1y", user_id="analyst-9", title="Custom"
        )
        await generate_png_export(req)
        assert _FakePngExporter.last_request is req

    @pytest.mark.asyncio
    async def test_does_not_mark_failed_on_success(self) -> None:
        _FakePngExporter.result = _canned_png_result()
        req = ChartRequest(timeframe="30d")
        await generate_png_export(req)
        repo = _FakeHistoryRepo.instances[0]
        assert repo.failed == []

    @pytest.mark.asyncio
    async def test_user_id_none_is_recorded_as_none(self) -> None:
        _FakePngExporter.result = _canned_png_result()
        req = ChartRequest(timeframe="30d")
        await generate_png_export(req)
        repo = _FakeHistoryRepo.instances[0]
        assert repo.created[0].user_id is None


# ============================================================
# PNG — FAILURE PATH
# ============================================================
class TestGeneratePngExportFailurePath:
    """generate_png_export: exporter raises → mark_failed + re-raise."""

    @pytest.mark.asyncio
    async def test_re_raises_the_original_exception(self) -> None:
        _FakePngExporter.raises = ValueError("boom")
        req = ChartRequest(timeframe="30d")
        with pytest.raises(ValueError, match="boom"):
            await generate_png_export(req)

    @pytest.mark.asyncio
    async def test_marks_failed(self) -> None:
        _FakePngExporter.raises = ValueError("boom")
        req = ChartRequest(timeframe="30d")
        with pytest.raises(ValueError):
            await generate_png_export(req)

        repo = _FakeHistoryRepo.instances[0]
        assert repo.failed == [1]

    @pytest.mark.asyncio
    async def test_does_not_mark_completed(self) -> None:
        _FakePngExporter.raises = ValueError("boom")
        req = ChartRequest(timeframe="30d")
        with pytest.raises(ValueError):
            await generate_png_export(req)

        repo = _FakeHistoryRepo.instances[0]
        assert repo.completed == []

    @pytest.mark.asyncio
    async def test_mark_failed_does_not_mask_the_original_error(self) -> None:
        _FakePngExporter.raises = ValueError("original error")
        _FakeHistoryRepo.mark_failed_raises = RuntimeError("cleanup boom")

        req = ChartRequest(timeframe="30d")
        with pytest.raises(ValueError, match="original error"):
            await generate_png_export(req)

    @pytest.mark.asyncio
    async def test_mark_failed_is_still_attempted(self) -> None:
        _FakePngExporter.raises = ValueError("original error")
        _FakeHistoryRepo.mark_failed_raises = RuntimeError("cleanup boom")

        req = ChartRequest(timeframe="30d")
        with pytest.raises(ValueError):
            await generate_png_export(req)

        repo = _FakeHistoryRepo.instances[0]
        # The mark_failed call was attempted (and raised) — the
        # fake records the id before raising.
        assert repo.failed == [1]