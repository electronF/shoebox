"""
Disk-based implementation of IFileStorage.

Files are stored under settings.upload_path with a SHA-256-based
name to ensure deduplication: uploading the same file twice
results in a single file on disk.
"""

import hashlib
import logging
from datetime import date
from pathlib import Path

from backend.core.config import settings
from backend.core.interfaces import IFileStorage

logger = logging.getLogger(__name__)


class DiskFileStorage(IFileStorage):
    """
    Stores uploaded files on the local filesystem.

    The storage path format is:
        <upload_dir>/<YYYYMMDD>_<sha256[:12]>_<original_stem><ext>

    This format guarantees:
    - No filename collisions across uploads on the same day.
    - Deduplication: identical content produces the same path.
    - Human-readable filenames that retain the original name.

    Args:
        base_directory: Root directory for file storage.
                        Defaults to settings.upload_path.
    """

    def __init__(self, base_directory: Path | None = None) -> None:
        self._base_directory = base_directory or settings.upload_path
        self._base_directory.mkdir(parents=True, exist_ok=True)

    def save(self, filename: str, content: bytes) -> str:
        """
        Saves file content to disk and returns its absolute storage path.

        If a file with the same content already exists (same hash),
        the existing path is returned without writing again.

        Args:
            filename: Original filename including extension.
            content:  Raw bytes of the file.

        Returns:
            Absolute path string of the stored file.
        """
        sha256_prefix = hashlib.sha256(content).hexdigest()[:12]
        today_str     = date.today().strftime("%Y%m%d")
        original      = Path(filename)
        safe_stem     = original.stem[:40]                 # truncate long names
        extension     = original.suffix.lower()

        storage_filename = f"{today_str}_{sha256_prefix}_{safe_stem}{extension}"
        destination      = self._base_directory / storage_filename

        if destination.exists():
            logger.debug("File already exists, skipping write: %s", destination)
        else:
            destination.write_bytes(content)
            logger.info("File saved: %s (%d bytes)", destination, len(content))

        return str(destination.resolve())

    def exists(self, storage_path: str) -> bool:
        """
        Checks whether a file exists at the given path.

        Args:
            storage_path: Absolute path as returned by save().

        Returns:
            True if the file exists on disk.
        """
        return Path(storage_path).exists()