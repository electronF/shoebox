"""
Parser for XLSX invoice files (multi-row, one row = one invoice/transaction).

Expects columns in this order: client, description, amount, date_sent, date_paid.
Extra columns are ignored. Rows with no amount are skipped.
"""

import logging
from datetime import date, datetime
from pathlib import Path

import openpyxl

from backend.core.enums import Category, EntryMethod, ValidationStatus
from backend.core.models import Transaction
from backend.infrastructure.parsers.base import BaseParser

logger = logging.getLogger(__name__)

# Column indices (0-based) for the expected XLSX layout
_COL_CLIENT      = 0
_COL_DESCRIPTION = 1
_COL_AMOUNT      = 2
_COL_DATE_SENT   = 3
_COL_DATE_PAID   = 4

_DATE_FORMATS = ("%m/%d/%Y", "%b %d, %y", "%b %d %Y", "%B %d, %Y", "%b %d - %Y")


def _parse_date(raw_value) -> date | None:
    """
    Parses a date value from an Excel cell.

    Handles Python date objects (already parsed by openpyxl),
    datetime objects, and common string date formats.

    Args:
        raw_value: Cell value as returned by openpyxl.

    Returns:
        A date object, or None if parsing failed.
    """
    if raw_value is None:
        return None
    if isinstance(raw_value, date):
        return raw_value
    if isinstance(raw_value, datetime):
        return raw_value.date()
    # Try string formats
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(str(raw_value).strip(), fmt).date()
        except ValueError:
            continue
    logger.warning("Could not parse date value: '%s'", raw_value)
    return None


class XLSXParser(BaseParser):
    """
    Parses multi-row XLSX files into Transaction domain objects.

    Each data row (starting from row 2, skipping header) becomes
    one Transaction. Rows where the amount cell is empty are skipped.
    Invoice amounts are stored as negative numbers (credits to the business)
    to distinguish them from expenses in analytics queries.
    """

    def can_parse(self, filename: str) -> bool:
        """Returns True for .xlsx files."""
        return Path(filename).suffix.lower() == ".xlsx"

    def _parse_impl(
        self, file_path: str, source_id: str, file_id: str
    ) -> list[Transaction]:
        """
        Reads all data rows from the first worksheet.

        Args:
            file_path: Path to the .xlsx file.
            source_id: Payment source ID.
            file_id:   Uploaded file ID.

        Returns:
            List of Transaction objects, one per valid data row.
        """
        workbook  = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        worksheet = workbook.worksheets[0]

        transactions: list[Transaction] = []

        for row_index, row in enumerate(
            worksheet.iter_rows(min_row=2, values_only=True), start=2
        ):
            if not row or row[_COL_AMOUNT] is None:
                continue

            try:

                raw_amount   = row[_COL_AMOUNT]
                raw_desc     = row[_COL_DESCRIPTION] or row[_COL_CLIENT]
                raw_date     = row[_COL_DATE_SENT]

                if raw_amount is None:
                    continue

                try:
                    amount      = float(str(raw_amount))
                    description = str(raw_desc) if raw_desc is not None else "Invoice"
                    tx_date     = _parse_date(raw_date) or date.today()
                except (TypeError, ValueError) as exc:
                    logger.warning(
                        "XLSXParser: skipping row %d in '%s': %s",
                        row_index, file_path, exc,
                    )
                    continue
                # amount      = float(row[_COL_AMOUNT])
                # description = str(row[_COL_DESCRIPTION] or row[_COL_CLIENT] or "Invoice")
                # tx_date     = _parse_date(row[_COL_DATE_SENT]) or date.today()

                
            except (TypeError, ValueError) as exc:
                logger.warning(
                    "XLSXParser: skipping row %d in '%s': %s",
                    row_index, file_path, exc,
                )
                continue

            transactions.append(Transaction(
                id=None,
                date=tx_date,
                description=description,
                amount=-abs(amount),      # invoices are income (negative expense)
                category=Category.UNCATEGORIZED,
                source_id=source_id,
                file_id=file_id,
                ref=None,
                entry_method=EntryMethod.PARSED,
                ocr_confidence=None,
                validation_status=ValidationStatus.OK,
            ))

        workbook.close()
        logger.info(
            "XLSXParser: %d rows parsed from '%s'",
            len(transactions), file_path,
        )
        return transactions