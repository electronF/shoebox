"""
Shoebox domain business enumerations.

These enums are the source of truth for accepted values.
They are used in dataclasses, ORMs, and Pydantic schemas.
"""

from enum import Enum


class Category(str, Enum):
    """Expense categories for transaction classification."""

    SOFTWARE      = "Software & Subscriptions"
    COWORKING     = "Coworking"
    ECOMMERCE     = "Ecommerce"
    SUPPLIES      = "Supplies & Shipping"
    MEALS         = "Business Meals"
    TRANSPORT     = "Transport"
    PERSONAL      = "Personal (Excluded)"
    UNCATEGORIZED = "Uncategorized"

    


class SourceType(str, Enum):
    """Type of payment source."""

    CREDIT_CARD = "credit_card"
    CASH        = "cash"
    PERSONAL    = "personal"


class FileType(str, Enum):
    """Type of physical file uploaded."""

    PDF   = "pdf"
    IMAGE = "image"
    XLSX  = "xlsx"
    TXT   = "txt"


class DocType(str, Enum):
    """
    Business document type — determines the parser and expected fields.
    Matches the generated ID prefixes.
    """

    RECEIPT   = "REC"   # Receipt / Received invoice (expense)
    STATEMENT = "STMT"  # Bank or card statement
    INVOICE   = "INV"   # Issued invoice (income)
    NOTES     = "NOTE"  # Text notes file


class EntryMethod(str, Enum):
    """
    Method by which a transaction was created.
    Used for icon display in the history.
    """

    OCR    = "ocr"      # Extracted via OCR from an image
    PARSED = "parsed"   # Parsed from structured PDF or XLSX
    MANUAL = "manual"   # Entered directly by the user


class ValidationStatus(str, Enum):
    """Validation status of a transaction after ingestion."""

    PENDING  = "pending"   # Awaiting verification
    OK       = "ok"        # Validated without issues
    WARNING  = "warning"   # Non-blocking warning
    ERROR    = "error"     # Error requiring correction
    INFORMAL = "informal"  # Informal receipt, missing taxes accepted


class InvoiceStatus(str, Enum):
    """Payment status of an issued invoice."""

    PAID    = "paid"
    UNPAID  = "unpaid"
    OVERDUE = "overdue"
    VOID    = "void"


class AnomalyType(str, Enum):
    """Types of automatically detected anomalies."""

    DUPLICATE          = "duplicate"
    PERSONAL_ON_BIZ    = "personal_on_biz_card"
    TAX_MISMATCH       = "tax_mismatch"
    UNUSUAL_AMOUNT     = "unusual_amount"
    FUTURE_DATE        = "future_date"
    WRONG_FILE_TYPE    = "wrong_file_type"


class RecurrenceFrequency(str, Enum):
    """Frequency classification for a detected recurring expense pattern."""

    MONTHLY  = "monthly"   # same amount every month
    VARIABLE = "variable"  # appears monthly but amount varies
    ANNUAL   = "annual"    # appears once per year
    ONCE     = "once"      # single occurrence, not recurring