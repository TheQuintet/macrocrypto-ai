"""Export file storage.

Stores the byte payloads produced by the CSV, PNG, and PDF
exporters (A2.2–A2.4) so they can be served later by a download
endpoint (A2.6). The storage layer is deliberately narrow:

    - ``ExportStorage`` is a Protocol. Anything that implements
      ``save``, ``load``, ``delete``, ``exists``, and ``list`` is a
      valid storage backend.
    - ``LocalDiskStorage`` is the A2.6 implementation. Files live
      under ``settings.export_storage_dir_path``.
    - ``InMemoryStorage`` is a test fake. It holds files in a dict
      and never touches the filesystem.

Design:

    - Storage keys are opaque strings. The exporters already
      generate filenames via their ``_filename`` helpers, and those
      filenames are what the ``export_history.file_name`` column
      records, so keys == filenames on this branch. A future S3
      backend could layer a prefix on top without changing the
      protocol.
    - ``save`` is synchronous. Local disk writes are fast and this
      service does not currently run a thread pool for I/O. If a
      future backend needs async (S3, GCS), the protocol can be
      widened then — this branch does not need it.
    - Path traversal is rejected: a key containing ``..``, an
      absolute path component, or a path separator that would
      escape the storage root raises ``ValueError``. The
      exporters never produce such keys, but the guard prevents a
      future caller from turning a user-supplied filename into a
      read or write anywhere on disk.
    - ``list`` returns keys, not paths, and is used by the cleanup
      job (A2.6 Group 3) to find files older than the TTL. It
      does not recurse into subdirectories.
    - ``LocalDiskStorage`` exposes ``path_for(key)`` and
      ``mtime(key)`` as extras beyond the protocol. The download
      endpoint uses ``path_for`` to serve a file via FastAPI's
      ``FileResponse``, and the cleanup job uses ``mtime`` to
      decide expiry. Neither is on the protocol: a future S3
      backend would serve via a presigned URL and expire via
      bucket lifecycle policies, not by exposing a filesystem
      path or an mtime.

Usage:

    from app.export.storage import get_storage

    storage = get_storage()
    storage.save("macro-crypto-btc_price-30d-2026-09-16.csv", payload)
    data = storage.load("macro-crypto-btc_price-30d-2026-09-16.csv")
    storage.delete("macro-crypto-btc_price-30d-2026-09-16.csv")
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Protocol, runtime_checkable

from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# KEY VALIDATION
# ============================================================
# A key is a single filename: no directory separators, no
# parent-directory references, no empty string. The exporters
# produce keys in this shape; the guard exists for future callers.
_SAFE_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._\-]+$")


def _validate_key(key: str) -> None:
    """Raise ValueError if ``key`` is not a safe storage key.

    A safe key is a non-empty string containing only ASCII letters,
    digits, dots, underscores, and hyphens, and it must not be
    ``"."`` or ``".."`` (those resolve to directory references, not
    files). In particular, a safe key must not contain ``/`` or
    ``\\``.

    Args:
        key: The storage key to validate.

    Raises:
        ValueError: If the key is empty, is a bare ``"."`` / ``".."``,
            or contains unsafe characters.
    """
    if not key:
        raise ValueError("storage key must be non-empty")
    if key in (".", ".."):
        raise ValueError(
            f"storage key {key!r} is a directory reference, not a file"
        )
    if not _SAFE_KEY_PATTERN.match(key):
        raise ValueError(
            f"storage key {key!r} contains unsafe characters; "
            f"keys must match {_SAFE_KEY_PATTERN.pattern}"
        )


# ============================================================
# PROTOCOL
# ============================================================
@runtime_checkable
class ExportStorage(Protocol):
    """Storage backend protocol for export payloads.

    Implementations must be safe to call concurrently from a single
    asyncio event loop. They are not required to be thread-safe.
    """

    def save(self, key: str, data: bytes) -> int:
        """Persist ``data`` under ``key``.

        Overwrites an existing file with the same key.

        Args:
            key: The storage key (a filename).
            data: The bytes to store.

        Returns:
            The number of bytes written, which equals ``len(data)``.

        Raises:
            ValueError: If the key is unsafe.
            OSError: If the underlying storage fails.
        """
        ...

    def load(self, key: str) -> bytes:
        """Read the bytes stored under ``key``.

        Args:
            key: The storage key.

        Returns:
            The stored bytes.

        Raises:
            ValueError: If the key is unsafe.
            FileNotFoundError: If no file exists for the key.
            OSError: If the underlying storage fails.
        """
        ...

    def delete(self, key: str) -> bool:
        """Remove the file stored under ``key``.

        Args:
            key: The storage key.

        Returns:
            True if a file was removed, False if it did not exist.

        Raises:
            ValueError: If the key is unsafe.
            OSError: If the underlying storage fails.
        """
        ...

    def exists(self, key: str) -> bool:
        """Return True if a file exists for ``key``.

        Args:
            key: The storage key.

        Raises:
            ValueError: If the key is unsafe.
        """
        ...

    def list(self) -> List[str]:
        """Return the keys currently stored.

        Order is unspecified. Returns an empty list when the
        storage is empty.

        Raises:
            OSError: If the underlying storage fails.
        """
        ...


# ============================================================
# LOCAL DISK IMPLEMENTATION
# ============================================================
class LocalDiskStorage:
    """Store export payloads under a single directory on disk.

    The directory is created on first use. Files are written
    atomically: bytes go to a temporary file in the same directory,
    then the temp file is renamed onto the target key. A crash
    between the two steps leaves a stale ``.tmp`` file rather than
    a partially-written export.
    """

    def __init__(self, root: Path) -> None:
        """Initialize the storage.

        Args:
            root: Directory to store files under. Created if it
                does not exist.
        """
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalDiskStorage root: {self._root}")

    @property
    def root(self) -> Path:
        """The storage root directory."""
        return self._root

    def save(self, key: str, data: bytes) -> int:
        """Persist ``data`` under ``key``, atomically.

        Writes to a temporary file in the same directory, then
        renames it onto the target. A failure between the write and
        the rename leaves a ``.tmp`` file rather than a partial
        export.
        """
        _validate_key(key)
        target = self._root / key
        tmp = self._root / f".{key}.tmp"

        try:
            tmp.write_bytes(data)
            tmp.replace(target)
        except Exception:
            # Best-effort cleanup of the temp file; do not mask
            # the original error.
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass
            raise

        logger.debug(f"Stored {len(data)} bytes at {key}")
        return len(data)

    def load(self, key: str) -> bytes:
        """Read the bytes stored under ``key``."""
        _validate_key(key)
        target = self._root / key
        return target.read_bytes()

    def delete(self, key: str) -> bool:
        """Remove the file stored under ``key``."""
        _validate_key(key)
        target = self._root / key
        if not target.exists():
            return False
        target.unlink()
        return True

    def exists(self, key: str) -> bool:
        """Return True if a file exists for ``key``."""
        _validate_key(key)
        return (self._root / key).exists()

    def list(self) -> List[str]:
        """Return the keys currently stored.

        Skips temp files (those beginning with ``.``) so an
        in-progress write does not appear in the listing.
        """
        return sorted(
            p.name
            for p in self._root.iterdir()
            if p.is_file() and not p.name.startswith(".")
        )

    def path_for(self, key: str) -> Path:
        """Return the absolute filesystem path for ``key``.

        Helper for the download endpoint, which serves files via
        FastAPI's ``FileResponse`` (a streaming response). Not
        part of the ``ExportStorage`` protocol — callers that need
        it should hold a ``LocalDiskStorage`` reference directly.

        The returned path is not checked for existence here; the
        endpoint is expected to call ``exists`` (or catch
        ``FileNotFoundError`` from ``FileResponse``) separately.

        Raises:
            ValueError: If the key is unsafe.
        """
        _validate_key(key)
        return self._root / key

    def mtime(self, key: str) -> float:
        """Return the modification time of ``key`` as a UNIX timestamp.

        Helper for the cleanup job. Not part of the ``ExportStorage``
        protocol — callers that need it should hold a
        ``LocalDiskStorage`` reference directly.

        Raises:
            ValueError: If the key is unsafe.
            FileNotFoundError: If no file exists for the key.
        """
        _validate_key(key)
        return (self._root / key).stat().st_mtime


# ============================================================
# IN-MEMORY FAKE (tests)
# ============================================================
class InMemoryStorage:
    """In-memory implementation of ``ExportStorage`` for tests.

    Never touches the filesystem. Bytes are held in a dict keyed
    by the storage key. A ``mtime`` map records the write time for
    each key so the cleanup job's tests can drive expiry without
    sleeping.
    """

    def __init__(self) -> None:
        self._files: Dict[str, bytes] = {}
        self._mtimes: Dict[str, float] = {}

    def save(self, key: str, data: bytes) -> int:
        _validate_key(key)
        self._files[key] = bytes(data)
        # Monotonically increasing mtime so successive saves are
        # distinguishable in tests without sleeping.
        prev = max(self._mtimes.values(), default=0.0)
        self._mtimes[key] = prev + 1.0
        return len(data)

    def load(self, key: str) -> bytes:
        _validate_key(key)
        if key not in self._files:
            raise FileNotFoundError(key)
        return self._files[key]

    def delete(self, key: str) -> bool:
        _validate_key(key)
        if key not in self._files:
            return False
        del self._files[key]
        self._mtimes.pop(key, None)
        return True

    def exists(self, key: str) -> bool:
        _validate_key(key)
        return key in self._files

    def list(self) -> List[str]:
        return sorted(self._files.keys())

    def mtime(self, key: str) -> float:
        """Return the recorded mtime for ``key`` (test helper)."""
        _validate_key(key)
        if key not in self._mtimes:
            raise FileNotFoundError(key)
        return self._mtimes[key]


# ============================================================
# FACTORY
# ============================================================
_storage_singleton: Optional[ExportStorage] = None


def get_storage(
    backend: Optional[str] = None,
    *,
    force_new: bool = False,
) -> ExportStorage:
    """Return the configured storage backend.

    On first call (or when ``force_new=True``), a new backend
    instance is created from settings. Subsequent calls return the
    cached singleton unless ``force_new`` is set, which is what
    tests use to reset between runs.

    Args:
        backend: Override the configured backend name. One of
            ``"local"`` or ``"memory"``. Defaults to
            ``settings.export_storage_backend``.
        force_new: When True, ignore the cached singleton and build
            a fresh backend.

    Returns:
        An object implementing the ``ExportStorage`` protocol.

    Raises:
        ValueError: If ``backend`` is not a known name.
    """
    global _storage_singleton

    if _storage_singleton is not None and not force_new:
        return _storage_singleton

    name = backend if backend is not None else settings.export_storage_backend

    if name == "local":
        storage: ExportStorage = LocalDiskStorage(
            settings.export_storage_dir_path
        )
    elif name == "memory":
        storage = InMemoryStorage()
    else:
        raise ValueError(
            f"Unknown export storage backend {name!r}. "
            f"Must be one of 'local', 'memory'."
        )

    _storage_singleton = storage
    return storage


__all__ = [
    "ExportStorage",
    "InMemoryStorage",
    "LocalDiskStorage",
    "get_storage",
]