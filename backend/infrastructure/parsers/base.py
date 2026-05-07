"""
Base class for all file parsers.

Provides a uniform error-handling wrapper around the concrete
parse logic so individual parsers only need to implement
_parse_impl() without repeating try/except boilerplate.
"""

import logging
from abc import abstractmethod

from backend.core.interfaces import IParser
from backend.core.models import Transaction

logger = logging.getLogger(__name__)


class BaseParser(IParser):
    """
    Abstract base parser with built-in exception handling.

    Subclasses implement _parse_impl() with the actual extraction logic.
    If _parse_impl() raises any exception, parse() logs the error
    and returns an empty list rather than crashing the ingestion pipeline.
    """

    def parse(self, file_path: str, source_id: str, file_id: str) -> list[Transaction]:
        """
        Parses a file and returns extracted transactions.

        Wraps _parse_impl() in a try/except so a single broken file
        does not abort the processing of the other uploaded files.

        Args:
            file_path: Absolute path to the file on disk.
            source_id: ID of the associated payment source.
            file_id:   ID of the uploaded file record (for traceability).

        Returns:
            List of Transaction objects. Empty list on parse failure.
        """
        try:
            return self._parse_impl(file_path, source_id, file_id)
        except Exception as exc:
            logger.error(
                "[%s] Failed to parse '%s': %s",
                self.__class__.__name__,
                file_path,
                exc,
                exc_info=True,
            )
            return []

    @abstractmethod
    def _parse_impl(
        self, file_path: str, source_id: str, file_id: str
    ) -> list[Transaction]:
        """
        Concrete parsing logic to implement in each subclass.

        Args:
            file_path: Absolute path to the file on disk.
            source_id: Payment source ID.
            file_id:   Uploaded file record ID.

        Returns:
            List of extracted Transaction domain objects.
        """
        ...