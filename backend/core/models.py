"""
Business domain models (pure dataclasses).

These classes represent business entities without any dependency
on SQLAlchemy, Pydantic, or FastAPI. They constitute the heart of the
domain (DIP principle: external layers depend on them, not the other way around).
"""

from dataclasses import dataclass, field
from datetime import date as dateT, datetime, timezone
from typing import Optional

from .enums import (
    AnomalyType,
    Category,
    DocType,
    EntryMethod,
    FileType,
    InvoiceStatus,
    SourceType,
    ValidationStatus,
)


@dataclass
class PaymentSource:
    """Payment source (card, cash, personal)."""

    id:          Optional[str]
    label:       str
    source_type: SourceType
    last_four:   Optional[str]
    created_at:  dateT


@dataclass
class UploadedFile:
    """
    Metadata of a file ingested into the system.

    Links a physical file to a payment source and 
    tracks the transactions extracted from it.
    """

    id:            Optional[str]
    filename:      str
    file_type:     FileType
    doc_type:      DocType
    storage_path:  str
    source_id:     Optional[str]
    uploaded_at:   dateT
    tx_count:      int   = 0
    total_amount:  float = 0.0
    ocr_attempted: bool  = False
    ocr_success:   bool  = False


@dataclass
class Transaction:
    """
    Financial transaction — expense or credit.

    Can originate from a PDF statement, an image receipt (OCR),
    an XLSX, or manual entry.
    """

    id:                Optional[str]
    date:              dateT
    description:       str
    amount:            float         # negative = refund / credit
    category:          Category
    source_id:         str
    file_id:           Optional[str]
    ref:               Optional[str]
    entry_method:      EntryMethod
    ocr_confidence:    Optional[float]   # 0.0–1.0, None if non-OCR
    validation_status: ValidationStatus
    is_personal:       bool  = False
    is_informal:       bool  = False     # informal receipt without taxes accepted
    is_flagged:        bool  = False
    flag_reason:       Optional[str] = None
    created_at:        datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Invoice:
    """Invoice issued by the freelancer (income)."""

    id:          Optional[str]
    client:      str
    description: str
    amount:      float
    date_sent:   Optional[dateT]
    date_paid:   Optional[dateT]
    status:      InvoiceStatus
    file_id:     Optional[str]
    created_at:  datetime = field(default_factory=datetime.utcnow)


@dataclass
class Anomaly:
    """
    Anomaly automatically detected on a transaction.

    Separated from Transaction to avoid the proliferation of
    flag columns in the main table.
    """

    id:             Optional[str]
    transaction_id: str
    anomaly_type:   AnomalyType
    description:    str
    resolved:       bool = False
    detected_at:    dateT = field(default_factory=dateT.today)


@dataclass
class ActionItem:
    """Task extracted from notes.txt or entered manually."""

    id:          Optional[str]
    text:        str
    status:      str        # "open" | "done"
    source_file: Optional[str]
    created_at:  dateT
