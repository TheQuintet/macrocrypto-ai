"""Unit tests for daily_export_cleanup_job.

Covers:
    - Skip-on-non-local-backend (a backend without ``mtime``)
    - Delete-expired-files path
    - Keep-fresh-files path
    - Mixed delete/keep classification
    - Per-key error isolation (stat failure, delete failure)
    - Vanished file during the loop
    - list() failure raises RuntimeError
    - Summary shape

The job reads storage via ``get_storage`` and settings for the TTL.
Both are monkeypatched so the tests never touch real storage and
never wait for real time to pass. The InMemoryStorage fake's
monotonic mtimes give us deterministic "old" and "fresh" files
without sleeping.

Time is pinned via a local ``freeze_cleanup_time`` fixture. The
cleanup job does ``import time`` inside the function body (matching
the other jobs in ``app.scheduler.jobs``), so the module object is
the stdlib ``time`` module. We patch ``time.time`` on that module
directly; ``monkeypatch`` reverts it at the end of each test, so
the effect is scoped to the test that requested it.
"""

import time
from typing import Any, Dict
from unittest.mock import patch

import pytest

from app.export.storage import (
    InMemoryStorage,
    LocalDiskStorage,
)
from app.scheduler.jobs import daily_export_cleanup_job


# ============================================================
# HELPERS
# ============================================================
class _ClockStorage(InMemoryStorage):
    """InMemoryStorage with a controllable mtime for each key.

    The parent class assigns monotonically increasing mtimes on
    every save (1.0, 2.0, 3.0, ...). For the cleanup job we need
    to place files at specific ages relative to ``now()``, so we
    override both ``save`` (to skip the parent's mtime
    bookkeeping) and ``mtime`` (to read from our own map).

    A key that is saved but never had ``set_mtime`` called has no
    mtime, which the cleanup job treats as "vanished" — that's the
    branch ``test_vanished_file_is_counted_separately`` exercises.
    """

    def __init__(self, now: float) -> None:
        super().__init__()
        self._now = now
        self._mtimes: Dict[str, float] = {}

    def save(self, key: str, data: bytes) -> int:
        # Store bytes in the parent's dict but do NOT register an
        # mtime. The cleanup-job tests always set mtimes explicitly
        # via set_mtime(); a saved-but-never-stamped key has no
        # mtime at all.
        self._files[key] = bytes(data)
        return len(data)

    def set_mtime(self, key: str, mtime: float) -> None:
        self._mtimes[key] = mtime

    def mtime(self, key: str) -> float:
        if key not in self._mtimes:
            raise FileNotFoundError(key)
        return self._mtimes[key]


class _NoMtimeStorage:
    """Minimal storage-like fake without an ``mtime`` method.

    Used to exercise the job's "backend does not support age-based
    cleanup" branch. ``InMemoryStorage`` deliberately has ``mtime``
    (the cleanup-job tests use it), so it is not suitable here.
    """

    def __init__(self) -> None:
        self._files: Dict[str, bytes] = {}

    def save(self, key: str, data: bytes) -> int:
        self._files[key] = bytes(data)
        return len(data)

    def load(self, key: str) -> bytes:
        if key not in self._files:
            raise FileNotFoundError(key)
        return self._files[key]

    def delete(self, key: str) -> bool:
        return self._files.pop(key, None) is not None

    def exists(self, key: str) -> bool:
        return key in self._files

    def list(self):
        return sorted(self._files.keys())


# ============================================================
# FIXTURES
# ============================================================
@pytest.fixture()
def freeze_cleanup_time(monkeypatch):
    """Return a controller that pins the cleanup job's ``now``.

    ``daily_export_cleanup_job`` does ``import time`` inside its
    function body (matching the other jobs in
    ``app.scheduler.jobs``), so the ``time`` it sees is the stdlib
    module object. We patch ``time.time`` on that module directly;
    ``monkeypatch`` reverts the change at the end of the test.

    Returns a setter: ``set_now(t)`` pins the clock to ``t``.
    """
    state = {"now": time.time()}

    monkeypatch.setattr(time, "time", lambda: state["now"])

    def set_now(t: float) -> None:
        state["now"] = t

    return set_now


# ============================================================
# SKIP-ON-NON-LOCAL
# ============================================================
class TestSkipOnNonLocalBackend:
    """The job is a no-op when storage lacks an ``mtime`` method."""

    @pytest.mark.asyncio
    async def test_storage_without_mtime_is_skipped(self) -> None:
        storage = _NoMtimeStorage()
        storage.save("a.csv", b"x")

        with patch(
            "app.scheduler.jobs.get_storage", return_value=storage
        ):
            result = await daily_export_cleanup_job()

        assert result["backend"] == "_NoMtimeStorage"
        assert result["scanned"] == 0
        assert result["deleted"] == 0
        assert result["skipped_not_expired"] == 0
        assert result["failed"] == 0
        # The file is untouched.
        assert storage.exists("a.csv")

    @pytest.mark.asyncio
    async def test_ttl_is_still_reported(self, monkeypatch) -> None:
        from app.config import settings

        monkeypatch.setattr(settings, "export_file_ttl_seconds", 3600)

        with patch(
            "app.scheduler.jobs.get_storage",
            return_value=_NoMtimeStorage(),
        ):
            result = await daily_export_cleanup_job()

        assert result["ttl_seconds"] == 3600


# ============================================================
# HAPPY PATH — EXPIRY
# ============================================================
class TestExpiry:
    """Expired files are deleted; fresh files are kept."""

    @pytest.mark.asyncio
    async def test_all_fresh_files_are_kept(
        self, monkeypatch, freeze_cleanup_time
    ) -> None:
        now = time.time()
        freeze_cleanup_time(now)

        from app.config import settings
        monkeypatch.setattr(settings, "export_file_ttl_seconds", 3600)

        storage = _ClockStorage(now)
        # Two files, both written 60 seconds ago → kept.
        storage.save("a.csv", b"x")
        storage.save("b.csv", b"x")
        storage.set_mtime("a.csv", now - 60)
        storage.set_mtime("b.csv", now - 60)

        with patch(
            "app.scheduler.jobs.get_storage", return_value=storage
        ):
            result = await daily_export_cleanup_job()

        assert result["scanned"] == 2
        assert result["deleted"] == 0
        assert result["skipped_not_expired"] == 2
        assert result["failed"] == 0
        assert storage.exists("a.csv")
        assert storage.exists("b.csv")

    @pytest.mark.asyncio
    async def test_all_expired_files_are_deleted(
        self, monkeypatch, freeze_cleanup_time
    ) -> None:
        now = time.time()
        freeze_cleanup_time(now)

        from app.config import settings
        monkeypatch.setattr(settings, "export_file_ttl_seconds", 3600)

        storage = _ClockStorage(now)
        storage.save("old1.csv", b"x")
        storage.save("old2.csv", b"x")
        # Both written 7200 seconds ago (2 hours) → expired.
        storage.set_mtime("old1.csv", now - 7200)
        storage.set_mtime("old2.csv", now - 7200)

        with patch(
            "app.scheduler.jobs.get_storage", return_value=storage
        ):
            result = await daily_export_cleanup_job()

        assert result["scanned"] == 2
        assert result["deleted"] == 2
        assert result["skipped_not_expired"] == 0
        assert result["failed"] == 0
        assert not storage.exists("old1.csv")
        assert not storage.exists("old2.csv")

    @pytest.mark.asyncio
    async def test_mixed_expiry_classification(
        self, monkeypatch, freeze_cleanup_time
    ) -> None:
        now = time.time()
        freeze_cleanup_time(now)

        from app.config import settings
        monkeypatch.setattr(settings, "export_file_ttl_seconds", 3600)

        storage = _ClockStorage(now)
        storage.save("fresh.csv", b"x")
        storage.save("old.csv", b"x")
        storage.set_mtime("fresh.csv", now - 60)  # 1 min old
        storage.set_mtime("old.csv", now - 7200)  # 2 hours old

        with patch(
            "app.scheduler.jobs.get_storage", return_value=storage
        ):
            result = await daily_export_cleanup_job()

        assert result["scanned"] == 2
        assert result["deleted"] == 1
        assert result["skipped_not_expired"] == 1
        assert storage.exists("fresh.csv")
        assert not storage.exists("old.csv")

    @pytest.mark.asyncio
    async def test_boundary_mtime_is_kept(
        self, monkeypatch, freeze_cleanup_time
    ) -> None:
        """A file whose age exactly equals the TTL is kept."""
        now = time.time()
        freeze_cleanup_time(now)

        from app.config import settings
        monkeypatch.setattr(settings, "export_file_ttl_seconds", 3600)

        storage = _ClockStorage(now)
        storage.save("boundary.csv", b"x")
        storage.set_mtime("boundary.csv", now - 3600)

        with patch(
            "app.scheduler.jobs.get_storage", return_value=storage
        ):
            result = await daily_export_cleanup_job()

        # The job's comparison is ``mtime >= cutoff`` → kept.
        assert result["skipped_not_expired"] == 1
        assert result["deleted"] == 0


# ============================================================
# ERROR ISOLATION
# ============================================================
class TestErrorIsolation:
    """Per-key failures are counted, not raised."""

    @pytest.mark.asyncio
    async def test_stat_failure_counts_as_failed(
        self, monkeypatch, freeze_cleanup_time
    ) -> None:
        now = time.time()
        freeze_cleanup_time(now)

        from app.config import settings
        monkeypatch.setattr(settings, "export_file_ttl_seconds", 3600)

        storage = _ClockStorage(now)
        storage.save("a.csv", b"x")
        storage.set_mtime("a.csv", now - 60)
        # Override mtime to raise RuntimeError for one key, to
        # exercise the stat_failed branch. FileNotFoundError is
        # handled separately by the "vanished" branch.
        original_mtime = storage.mtime

        def bad_mtime(key: str) -> float:
            if key == "a.csv":
                raise RuntimeError("disk on fire")
            return original_mtime(key)

        storage.mtime = bad_mtime  # type: ignore[method-assign]

        with patch(
            "app.scheduler.jobs.get_storage", return_value=storage
        ):
            result = await daily_export_cleanup_job()

        assert result["failed"] == 1
        assert result["deleted"] == 0
        assert result["scanned"] == 1

    @pytest.mark.asyncio
    async def test_delete_failure_counts_as_failed(
        self, monkeypatch, freeze_cleanup_time
    ) -> None:
        now = time.time()
        freeze_cleanup_time(now)

        from app.config import settings
        monkeypatch.setattr(settings, "export_file_ttl_seconds", 3600)

        storage = _ClockStorage(now)
        storage.save("old.csv", b"x")
        storage.set_mtime("old.csv", now - 7200)

        def bad_delete(key: str) -> bool:
            raise RuntimeError("permission denied")

        storage.delete = bad_delete  # type: ignore[method-assign]

        with patch(
            "app.scheduler.jobs.get_storage", return_value=storage
        ):
            result = await daily_export_cleanup_job()

        assert result["failed"] == 1
        assert result["deleted"] == 0
        # File is still there.
        assert storage.exists("old.csv")

    @pytest.mark.asyncio
    async def test_vanished_file_is_counted_separately(
        self, monkeypatch, freeze_cleanup_time
    ) -> None:
        now = time.time()
        freeze_cleanup_time(now)

        from app.config import settings
        monkeypatch.setattr(settings, "export_file_ttl_seconds", 3600)

        storage = _ClockStorage(now)
        storage.save("gone.csv", b"x")
        # Deliberately do NOT call set_mtime — the cleanup-job
        # fake's save() does not register an mtime, so mtime()
        # raises FileNotFoundError, which the job treats as
        # "vanished".

        with patch(
            "app.scheduler.jobs.get_storage", return_value=storage
        ):
            result = await daily_export_cleanup_job()

        # Vanished files are neither deleted, kept, nor failed.
        assert result["deleted"] == 0
        assert result["skipped_not_expired"] == 0
        assert result["failed"] == 0
        assert result["scanned"] == 1
        assert result["results"]["gone.csv"]["status"] == "vanished"


# ============================================================
# LIST FAILURE
# ============================================================
class TestListFailure:
    """If we cannot even list, the job raises."""

    @pytest.mark.asyncio
    async def test_list_failure_raises_runtime_error(self) -> None:
        class _BrokenStorage(LocalDiskStorage):
            def list(self):
                raise OSError("disk unreadable")

        import tempfile
        from pathlib import Path

        tmp = Path(tempfile.mkdtemp())
        try:
            storage = _BrokenStorage(tmp)
            with patch(
                "app.scheduler.jobs.get_storage", return_value=storage
            ):
                with pytest.raises(RuntimeError, match="Cannot list"):
                    await daily_export_cleanup_job()
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)


# ============================================================
# SUMMARY SHAPE
# ============================================================
class TestSummaryShape:
    """The returned dict has all documented keys."""

    @pytest.mark.asyncio
    async def test_local_disk_empty_storage_summary(self, tmp_path) -> None:
        storage = LocalDiskStorage(tmp_path)

        with patch(
            "app.scheduler.jobs.get_storage", return_value=storage
        ):
            result = await daily_export_cleanup_job()

        expected_keys = {
            "backend",
            "scanned",
            "deleted",
            "skipped_not_expired",
            "failed",
            "ttl_seconds",
            "results",
            "elapsed_seconds",
        }
        assert set(result.keys()) == expected_keys
        assert result["backend"] == "LocalDiskStorage"
        assert result["scanned"] == 0
        assert result["deleted"] == 0
        assert result["skipped_not_expired"] == 0
        assert result["failed"] == 0
        assert isinstance(result["elapsed_seconds"], float)