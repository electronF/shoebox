"""
Parser for receipt images (printed or handwritten).

Uses Tesseract OCR via pytesseract to extract text from images,
then applies regex heuristics to find the vendor name, date, and total.
OCR confidence is estimated from Tesseract's word-level confidence data.
"""

import logging
import re
from datetime import datetime, date
from pathlib import Path

from PIL import Image
import pytesseract

from backend.core.enums import EntryMethod, ValidationStatus
from backend.core.models import Transaction
from backend.infrastructure.categorization.rules import categorize
from backend.infrastructure.parsers.base import BaseParser

logger = logging.getLogger(__name__)

_SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tiff"}

# Matches totals like: TOTAL: $40.80  or  **TOTAL: $12.00**
# _TOTAL_PATTERN = re.compile(
#     r"TOTAL\s*[:\*]?\s*\$?([\d,]+\.\d{2})", re.IGNORECASE
# )

_TOTAL_PATTERN = re.compile(
    r"(?<!SOUS[-\s])(?<!SUB[-\s])TOTAL\s*[:\*]?\s*\$?([\d,]+\.\d{2})",
    re.IGNORECASE,
)

# Matches dates in dd/mm/yyyy or yyyy-mm-dd format
_DATE_PATTERN = re.compile(
    r"(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})"
)

# Matches the first all-caps vendor name line (typical for printed receipts)
_VENDOR_PATTERN = re.compile(
    r"^([A-Z][A-Z\s'&\-]+(?:INC|LTD|LTÉE|SUPPLY|REST|CENTRAL|KITCHEN)?)",
    re.MULTILINE,
)

_DATE_FORMATS = ("%d/%m/%Y", "%Y-%m-%d")

# TPS/GST — handles "TPS (5%) $1.77", "TPS: $1.77", "GST 1.77", etc.
_TPS_PATTERN = re.compile(
    r"(?:TPS|T\.P\.S\.|GST|G\.S\.T\.)\s*(?:\([^)]*\))?\s*[:#]?\s*\$?([\d,]+\.\d{2})",
    re.IGNORECASE,
)
# TVQ/QST — handles "TVQ (9.975%) $3.54", "TVQ: $3.54", etc.
_TVQ_PATTERN = re.compile(
    r"(?:TVQ|T\.V\.Q\.|QST|Q\.S\.T\.)\s*(?:\([^)]*\))?\s*[:#]?\s*\$?([\d,]+\.\d{2})",
    re.IGNORECASE,
)
# Sous-total — handles "Sous-total $35.49", "SUBTOTAL: 35.49", etc.
_SUBTOTAL_PATTERN = re.compile(
    r"(?:SOUS[-\s]?TOTAL|SUBTOTAL|SUB[-\s]?TOTAL)\s*[:#]?\s*\$?([\d,]+\.\d{2})",
    re.IGNORECASE,
)
# Transaction ref — handles "Trans #: 20250122-0312-0947", "REF: ABC123", "APPROV 123456"
_REF_PATTERN = re.compile(
    r"(?:TRANS|REF|APPROV|AUTH|N[°o])\s*#?\s*:?\s*([A-Z0-9][A-Z0-9\-]{3,})",
    re.IGNORECASE,
)


class ImageReceiptParser(BaseParser):
    """
    Extracts transaction data from receipt images using Tesseract OCR.

    For printed official receipts: high confidence extraction of
    vendor, date, and total.

    For handwritten/informal receipts: partial extraction with low
    confidence — the transaction is flagged as informal so the user
    can review and correct fields in the UI.
    """

    @property
    def produces_ocr(self) -> bool:
        return True

    def can_parse(self, filename: str) -> bool:
        """Returns True for image file extensions supported by Tesseract."""
        return Path(filename).suffix.lower() in _SUPPORTED_EXTENSIONS

    def _parse_impl(
        self, file_path: str, source_id: str, file_id: str
    ) -> list[Transaction]:
        """
        Runs OCR on the image and extracts one transaction.

        Args:
            file_path: Path to the image file.
            source_id: Payment source ID.
            file_id:   Uploaded file ID.

        Returns:
            A list containing exactly one Transaction if a total amount
            was found, or an empty list if extraction failed entirely.
        """
        image = Image.open(file_path)

        # Extract text with confidence data for each word
        ocr_data = pytesseract.image_to_data(
            image,
            lang="fra+eng",
            output_type=pytesseract.Output.DICT,
        )
        full_text = pytesseract.image_to_string(image, lang="fra+eng")

        # Compute mean confidence from words with confidence > 0
        confidences = [
            int(c) for c in ocr_data["conf"]
            if str(c).isdigit() and int(c) > 0
        ]
        ocr_confidence = (sum(confidences) / len(confidences) / 100.0
                         if confidences else 0.0)

        # Amount extraction (required)
        total_match = _TOTAL_PATTERN.search(full_text)
        if not total_match:
            logger.warning(
                "ImageReceiptParser: no total found in '%s'", file_path
            )
            return []

        amount = float(total_match.group(1).replace(",", ""))

        # Date extraction (best effort)
        tx_date = date.today()
        date_match = _DATE_PATTERN.search(full_text)
        if date_match:
            for fmt in _DATE_FORMATS:
                try:
                    tx_date = datetime.strptime(date_match.group(1), fmt).date()
                    break
                except ValueError:
                    continue

        # Vendor extraction (best effort)
        vendor_match = _VENDOR_PATTERN.search(full_text)
        description  = (
            vendor_match.group(1).strip()
            if vendor_match
            else Path(file_path).stem
        )

        category, is_personal, is_flagged, flag_reason = categorize(
            description, amount
        )

        # Mark as informal if taxes were not detected
        has_taxes  = bool(re.search(r"TPS|TVQ|GST|QST|tax", full_text, re.IGNORECASE))
        is_informal = not has_taxes
        val_status  = ValidationStatus.WARNING if is_informal else ValidationStatus.OK

        transaction = Transaction(
            id=None,
            date=tx_date,
            description=description,
            amount=amount,
            category=category,
            source_id=source_id,
            file_id=file_id,
            ref=None,
            entry_method=EntryMethod.OCR,
            ocr_confidence=round(ocr_confidence, 2),
            validation_status=val_status,
            is_personal=is_personal,
            is_informal=is_informal,
            is_flagged=is_flagged,
            flag_reason=flag_reason,
        )

        logger.info(
            "ImageReceiptParser: extracted '%s' $%.2f (confidence %.0f%%) from '%s'",
            description, amount, ocr_confidence * 100, file_path,
        )
        return [transaction]

    def extract_receipt_data(self, file_path: str) -> dict:
        """
        Runs OCR once and returns all extractable receipt fields as a dict.

        Returns empty strings for fields that cannot be found, so the form
        can still be pre-populated with whatever is available.

        Args:
            file_path: Path to the image file.

        Returns:
            Dict with keys: merchant, date, total, subtotal, tps, tvq, ref,
            category, ocr_confidence.
        """
        image = Image.open(file_path)

        ocr_data = pytesseract.image_to_data(
            image, lang="fra+eng", output_type=pytesseract.Output.DICT,
        )
        full_text = pytesseract.image_to_string(image, lang="fra+eng")

        confidences = [
            int(c) for c in ocr_data["conf"]
            if str(c).isdigit() and int(c) > 0
        ]
        ocr_confidence = (sum(confidences) / len(confidences) / 100.0
                         if confidences else 0.0)

        def _grab(pattern: re.Pattern) -> str:
            m = pattern.search(full_text)
            return m.group(1).replace(",", "") if m else ""

        total_raw = _grab(_TOTAL_PATTERN)

        tx_date = date.today()
        date_match = _DATE_PATTERN.search(full_text)
        if date_match:
            for fmt in _DATE_FORMATS:
                try:
                    tx_date = datetime.strptime(date_match.group(1), fmt).date()
                    break
                except ValueError:
                    continue

        vendor_match = _VENDOR_PATTERN.search(full_text)
        merchant = (vendor_match.group(1).strip() if vendor_match
                    else Path(file_path).stem)

        category, _, _, _ = categorize(merchant, float(total_raw) if total_raw else 0.0)

        return {
            "merchant":       merchant,
            "date":           str(tx_date),
            "total":          total_raw,
            "subtotal":       _grab(_SUBTOTAL_PATTERN),
            "tps":            _grab(_TPS_PATTERN),
            "tvq":            _grab(_TVQ_PATTERN),
            "ref":            _grab(_REF_PATTERN),
            "category":       category.value,
            "ocr_confidence": round(ocr_confidence, 2),
        }