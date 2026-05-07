"""
Parser for bank/credit card statement PDF files.

Uses pdfplumber to extract raw text, then applies a regex pattern
to find individual transaction lines matching the Visa statement format.
"""

import logging
import re
from datetime import date
from pathlib import Path

import pdfplumber

from backend.core.enums import Category, EntryMethod, ValidationStatus
from backend.core.models import Transaction
from backend.infrastructure.categorization.rules import categorize
from backend.infrastructure.parsers.base import BaseParser

logger = logging.getLogger(__name__)

# Matches lines like: TXN-0103-001  Jan 03  GOOGLE *WORKSPACE  $8.28
_TRANSACTION_LINE_PATTERN = re.compile(
    r"(TXN-[\w-]+)\s+"
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{2})\s+"
    r"(.+?)\s+"
    r"([-]?\$[\d,]+\.\d{2})\s*$",
    re.MULTILINE,
)

_MONTH_NAME_TO_NUMBER: dict[str, int] = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
    "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}

# Statement year — in production this should be extracted from the PDF header
_STATEMENT_YEAR = 2025


class PDFStatementParser(BaseParser):
    """
    Parses credit card statement PDFs into Transaction domain objects.

    Supports the National Credit Union Visa statement format.
    Each matched line becomes one Transaction.
    """

    def can_parse(self, filename: str) -> bool:
        """Returns True for .pdf files."""
        return Path(filename).suffix.lower() == ".pdf"

    def _parse_impl(
        self, file_path: str, source_id: str, file_id: str
    ) -> list[Transaction]:
        """
        Extracts all transaction lines from a statement PDF.

        Args:
            file_path: Path to the PDF file.
            source_id: Payment source ID to attach to each transaction.
            file_id:   Uploaded file ID for traceability.

        Returns:
            List of Transaction objects, one per statement line.
        """
        with pdfplumber.open(file_path) as pdf:
            full_text = "\n".join(
                page.extract_text() or "" for page in pdf.pages
            )

        transactions: list[Transaction] = []

        for match in _TRANSACTION_LINE_PATTERN.finditer(full_text):
            ref, month_str, day_str, description, amount_str = match.groups()

            amount     = float(amount_str.replace("$", "").replace(",", ""))
            month      = _MONTH_NAME_TO_NUMBER[month_str]
            tx_date    = date(_STATEMENT_YEAR, month, int(day_str))
            description = description.strip()

            category, is_personal, is_flagged, flag_reason = categorize(
                description, amount
            )

            transactions.append(Transaction(
                id=None,
                date=tx_date,
                description=description,
                amount=amount,
                category=category,
                source_id=source_id,
                file_id=file_id,
                ref=ref,
                entry_method=EntryMethod.PARSED,
                ocr_confidence=None,
                validation_status=ValidationStatus.OK,
                is_personal=is_personal,
                is_flagged=is_flagged,
                flag_reason=flag_reason,
            ))

        logger.info(
            "PDFStatementParser: %d transactions extracted from '%s'",
            len(transactions),
            file_path,
        )
        return transactions