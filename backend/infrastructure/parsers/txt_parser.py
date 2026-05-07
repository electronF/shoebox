"""
Parser for plain-text notes files (notes.txt).

Does not produce Transaction objects — instead extracts [todo] and
[done] action items which are handled separately by the IngestionService.
"""

import logging
from pathlib import Path

from backend.core.models import ActionItem, Transaction
from backend.infrastructure.parsers.base import BaseParser

logger = logging.getLogger(__name__)


class TxtNotesParser(BaseParser):
    """
    Parses a notes.txt file and extracts action items.

    Lines prefixed with [todo] become open action items.
    Lines prefixed with [done] become completed action items.
    All other non-empty lines are stored as context notes (open status).

    Note: parse() intentionally returns an empty transaction list.
    The extracted action items are accessible via extract_action_items().
    """

    def can_parse(self, filename: str) -> bool:
        """Returns True for .txt files."""
        return Path(filename).suffix.lower() == ".txt"

    def _parse_impl(
        self, file_path: str, source_id: str, file_id: str
    ) -> list[Transaction]:
        """
        Notes files do not contain transactions.

        Returns an empty list intentionally. Use extract_action_items()
        to obtain the structured data from this file type.
        """
        return []

    def extract_action_items(
        self, file_path: str, source_filename: str
    ) -> list[ActionItem]:
        """
        Reads a notes file and extracts structured action items.

        Args:
            file_path:       Absolute path to the .txt file on disk.
            source_filename: Original filename for traceability metadata.

        Returns:
            List of ActionItem domain objects with status "open" or "done".

        Example input line::

            [todo] greenloop still hasn't paid invoice 2 — follow up
            [done] adobe plan downgraded feb 14, refund came through

        """
        from datetime import date as _date

        raw_text = Path(file_path).read_text(encoding="utf-8")
        action_items: list[ActionItem] = []

        for line in raw_text.splitlines():
            stripped = line.strip()

            if stripped.startswith("[todo]"):
                status = "open"
                text   = stripped[len("[todo]"):].strip()
            elif stripped.startswith("[done]"):
                status = "done"
                text   = stripped[len("[done]"):].strip()
            elif stripped and not stripped.startswith("==") and not stripped.startswith("-"):
                # Treat loose notes as open context items
                status = "open"
                text   = stripped
            else:
                continue

            if text:
                action_items.append(ActionItem(
                    id=None,
                    text=text,
                    status=status,
                    source_file=source_filename,
                    created_at=_date.today(),
                ))

        logger.info(
            "TxtNotesParser: %d action items extracted from '%s'",
            len(action_items), file_path,
        )
        return action_items