"""Unit tests for app.export.storage.

Covers:
    - LocalDiskStorage: save/load/delete/exists/list/mtime/path_for
    - LocalDiskStorage: key validation, atomic write, tmp cleanup
    - InMemoryStorage: save/load/delete/exists/list/mtime, monotonic
      mtimes
    - get_storage: default backend, override, caching, force_new,
      unknown backend raises, protocol check
    - _validate_key: rejects empty, absolute, traversal, separators,
      whitespace

Both concrete backends are exercised on this module so a
regression in either fails in one obvious place. The local-disk
tests use ``tmp_path`` — the pytest fixture that gives each test a
fresh empty directory — so they never touch the real
``./exports/``.
"""

import shutil
from pathlib import Path

import pytest

from app.export.storage import (
    ExportStorage,
    InMemoryStorage,
    LocalDiskStorage,
    get_storage,
)


# ============================================================
# KEY VALIDATION
# ============================================================
class TestKeyValidation:
    """Both backends reject unsafe keys the same way."""

    @pytest.mark.parametrize(
        "bad_key",
        [
            "",
            "../etc/passwd",
            "a/b.csv",
            "a\\b.csv",
            "a b.csv",
            "..",
            ".",
            "a\x00b",
            "a;b",
            "a|b",
            "a*b",
        ],
    )
    def test_local_disk_rejects_unsafe_key(self, tmp_path: Path, bad_key: str) -> None:
        storage = LocalDiskStorage(tmp_path)
        with pytest.raises(ValueError):
            storage.save(bad_key, b"data")

    @pytest.mark.parametrize(
        "bad_key",
        [
            "",
            "../etc/passwd",
            "a/b.csv",
            "a\\b.csv",
            "a b.csv",
            "..",
        ],
    )
    def test_in_memory_rejects_unsafe_key(self, bad_key: str) -> None:
        storage = InMemoryStorage()
        with pytest.raises(ValueError):
            storage.save(bad_key, b"data")

    @pytest.mark.parametrize(
        "good_key",
        [
            "a.csv",
            "macro-crypto-btc_price-30d-2026-09-16.csv",
            "file.with.dots.csv",
            "UPPER_case-1.2.3.csv",
            "a",
        ],
    )
    def test_both_backends_accept_safe_key(
        self, tmp_path: Path, good_key: str
    ) -> None:
        LocalDiskStorage(tmp_path).save(good_key, b"data")
        InMemoryStorage().save(good_key, b"data")


# ============================================================
# LOCAL DISK — ROUND TRIP
# ============================================================
class TestLocalDiskRoundTrip:
    """LocalDiskStorage: save, load, delete, exists, list."""

    def test_save_returns_length(self, tmp_path: Path) -> None:
        storage = LocalDiskStorage(tmp_path)
        assert storage.save("a.csv", b"hello") == 5
        assert storage.save("b.csv", b"") == 0

    def test_load_returns_stored_bytes(self, tmp_path: Path) -> None:
        storage = LocalDiskStorage(tmp_path)
        payload = b"data_type,time,close\nbtc_price,x,y\n"
        storage.save("a.csv", payload)
        assert storage.load("a.csv") == payload

    def test_load_missing_raises_file_not_found(self, tmp_path: Path) -> None:
        storage = LocalDiskStorage(tmp_path)
        with pytest.raises(FileNotFoundError):
            storage.load("missing.csv")

    def test_exists_true_after_save(self, tmp_path: Path) -> None:
        storage = LocalDiskStorage(tmp_path)
        storage.save("a.csv", b"x")
        assert storage.exists("a.csv") is True

    def test_exists_false_when_missing(self, tmp_path: Path) -> None:
        storage = LocalDiskStorage(tmp_path)
        assert storage.exists("nope.csv") is False

    def test_delete_returns_true_when_removed(self, tmp_path: Path) -> None:
        storage = LocalDiskStorage(tmp_path)
        storage.save("a.csv", b"x")
        assert storage.delete("a.csv") is True
        assert storage.exists("a.csv") is False

    def test_delete_returns_false_when_missing(self, tmp_path: Path) -> None:
        storage = LocalDiskStorage(tmp_path)
        assert storage.delete("nope.csv") is False

    def test_list_empty(self, tmp_path: Path) -> None:
        storage = LocalDiskStorage(tmp_path)
        assert storage.list() == []

    def test_list_returns_saved_keys_sorted(self, tmp_path: Path) -> None:
        storage = LocalDiskStorage(tmp_path)
        storage.save("b.csv", b"x")
        storage.save("a.csv", b"x")
        storage.save("c.csv", b"x")
        assert storage.list() == ["a.csv", "b.csv", "c.csv"]

    def test_save_overwrites_existing(self, tmp_path: Path) -> None:
        storage = LocalDiskStorage(tmp_path)
        storage.save("a.csv", b"old")
        storage.save("a.csv", b"new")
        assert storage.load("a.csv") == b"new"


# ============================================================
# LOCAL DISK — ATOMICITY
# ============================================================
class TestLocalDiskAtomicity:
    """LocalDiskStorage writes atomically via a temp file + rename."""

    def test_no_tmp_file_left_after_successful_save(
        self, tmp_path: Path
    ) -> None:
        storage = LocalDiskStorage(tmp_path)
        storage.save("a.csv", b"x")
        # The only file in the directory is the target.
        entries = sorted(p.name for p in tmp_path.iterdir())
        assert entries == ["a.csv"]

    def test_tmp_file_does_not_appear_in_list(self, tmp_path: Path) -> None:
        """A leftover .tmp file (from a crash) is skipped by list()."""
        storage = LocalDiskStorage(tmp_path)
        storage.save("a.csv", b"x")
        (tmp_path / ".b.csv.tmp").write_bytes(b"partial")
        assert storage.list() == ["a.csv"]


# ============================================================
# LOCAL DISK — EXTRAS
# ============================================================
class TestLocalDiskExtras:
    """path_for and mtime, which are outside the protocol."""

    def test_path_for_returns_target_path(self, tmp_path: Path) -> None:
        storage = LocalDiskStorage(tmp_path)
        p = storage.path_for("a.csv")
        assert p.name == "a.csv"
        assert p.parent == tmp_path
        assert p.is_absolute()

    def test_path_for_rejects_unsafe_key(self, tmp_path: Path) -> None:
        storage = LocalDiskStorage(tmp_path)
        with pytest.raises(ValueError):
            storage.path_for("../etc/passwd")

    def test_mtime_returns_positive_float(self, tmp_path: Path) -> None:
        storage = LocalDiskStorage(tmp_path)
        storage.save("a.csv", b"x")
        mt = storage.mtime("a.csv")
        assert isinstance(mt, float)
        assert mt > 0

    def test_mtime_raises_for_missing(self, tmp_path: Path) -> None:
        storage = LocalDiskStorage(tmp_path)
        with pytest.raises(FileNotFoundError):
            storage.mtime("missing.csv")

    def test_root_is_created_on_init(self, tmp_path: Path) -> None:
        root = tmp_path / "nested" / "deep"
        assert not root.exists()
        storage = LocalDiskStorage(root)
        assert root.exists()
        assert storage.root == root


# ============================================================
# IN-MEMORY
# ============================================================
class TestInMemoryStorage:
    """InMemoryStorage: full round trip, no filesystem."""

    def test_save_and_load(self) -> None:
        storage = InMemoryStorage()
        assert storage.save("a.csv", b"hello") == 5
        assert storage.load("a.csv") == b"hello"

    def test_load_missing_raises_file_not_found(self) -> None:
        storage = InMemoryStorage()
        with pytest.raises(FileNotFoundError):
            storage.load("missing.csv")

    def test_delete(self) -> None:
        storage = InMemoryStorage()
        storage.save("a.csv", b"x")
        assert storage.delete("a.csv") is True
        assert storage.delete("a.csv") is False

    def test_exists(self) -> None:
        storage = InMemoryStorage()
        assert storage.exists("a.csv") is False
        storage.save("a.csv", b"x")
        assert storage.exists("a.csv") is True

    def test_list_sorted(self) -> None:
        storage = InMemoryStorage()
        storage.save("c.csv", b"x")
        storage.save("a.csv", b"x")
        storage.save("b.csv", b"x")
        assert storage.list() == ["a.csv", "b.csv", "c.csv"]

    def test_mtime_is_monotonic(self) -> None:
        storage = InMemoryStorage()
        storage.save("a.csv", b"x")
        storage.save("b.csv", b"x")
        storage.save("c.csv", b"x")
        assert storage.mtime("a.csv") < storage.mtime("b.csv")
        assert storage.mtime("b.csv") < storage.mtime("c.csv")

    def test_mtime_raises_for_missing(self) -> None:
        storage = InMemoryStorage()
        with pytest.raises(FileNotFoundError):
            storage.mtime("missing.csv")

    def test_delete_removes_mtime(self) -> None:
        storage = InMemoryStorage()
        storage.save("a.csv", b"x")
        storage.delete("a.csv")
        with pytest.raises(FileNotFoundError):
            storage.mtime("a.csv")


# ============================================================
# FACTORY
# ============================================================
class TestGetStorage:
    """get_storage: default, override, caching, error paths."""

    def test_force_new_returns_local_by_default(self) -> None:
        storage = get_storage(force_new=True)
        assert isinstance(storage, LocalDiskStorage)

    def test_override_to_memory(self) -> None:
        storage = get_storage(backend="memory", force_new=True)
        assert isinstance(storage, InMemoryStorage)

    def test_singleton_is_cached(self) -> None:
        s1 = get_storage(backend="memory", force_new=True)
        s2 = get_storage()
        assert s1 is s2

    def test_force_new_creates_fresh_instance(self) -> None:
        s1 = get_storage(backend="memory", force_new=True)
        s2 = get_storage(backend="memory", force_new=True)
        assert s1 is not s2

    def test_unknown_backend_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown export storage"):
            get_storage(backend="bogus", force_new=True)

    def test_protocol_is_runtime_checkable(self) -> None:
        assert isinstance(InMemoryStorage(), ExportStorage)
        assert isinstance(get_storage(backend="memory", force_new=True), ExportStorage)