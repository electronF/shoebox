"""
SQLAlchemy ORM models — database table definitions.

These classes map Python objects to database tables.
Separate from core/models.py (pure dataclasses) to keep
the domain decoupled from the persistence layer.
Conversion between ORM and domain objects happens in repositories.py.
"""

from datetime import date as dateT, datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.infrastructure.db.database import Base


class PaymentSourceORM(Base):
    """Maps to the payment_sources table."""

    __tablename__ = "payment_sources"

    id:          Mapped[str]           = mapped_column(String(20),  primary_key=True)
    label:       Mapped[str]           = mapped_column(String(120), nullable=False, unique=True)
    source_type: Mapped[str]           = mapped_column(String(20),  nullable=False)
    last_four:   Mapped[Optional[str]] = mapped_column(String(4),   nullable=True)
    created_at:  Mapped[dateT]          = mapped_column(Date,        nullable=False)


class UploadedFileORM(Base):
    """Maps to the uploaded_files table."""

    __tablename__ = "uploaded_files"

    id:            Mapped[str]           = mapped_column(String(20),  primary_key=True)
    filename:      Mapped[str]           = mapped_column(String(255), nullable=False)
    file_type:     Mapped[str]           = mapped_column(String(20),  nullable=False)
    doc_type:      Mapped[str]           = mapped_column(String(10),  nullable=False)
    storage_path:  Mapped[str]           = mapped_column(String(512), nullable=False, unique=True)
    source_id:     Mapped[Optional[str]] = mapped_column(String(20),  ForeignKey("payment_sources.id"), nullable=True)
    uploaded_at:   Mapped[dateT]          = mapped_column(Date,        nullable=False)
    tx_count:      Mapped[int]           = mapped_column(Integer,     default=0)
    total_amount:  Mapped[float]         = mapped_column(Float,       default=0.0)
    ocr_attempted: Mapped[bool]          = mapped_column(Boolean,     default=False)
    ocr_success:   Mapped[bool]          = mapped_column(Boolean,     default=False)


class TransactionORM(Base):
    """Maps to the transactions table."""

    __tablename__ = "transactions"

    id:                Mapped[str]            = mapped_column(String(20),  primary_key=True)
    date:              Mapped[dateT]           = mapped_column(Date,        nullable=False)
    description:       Mapped[str]            = mapped_column(String(255), nullable=False)
    amount:            Mapped[float]          = mapped_column(Float,       nullable=False)
    category:          Mapped[str]            = mapped_column(String(40),  nullable=False, default="Non catégorisé")
    source_id:         Mapped[str]            = mapped_column(String(20),  ForeignKey("payment_sources.id"), nullable=False)
    file_id:           Mapped[Optional[str]]  = mapped_column(String(20),  ForeignKey("uploaded_files.id"),  nullable=True)
    ref:               Mapped[Optional[str]]  = mapped_column(String(64),  nullable=True)
    entry_method:      Mapped[str]            = mapped_column(String(20),  nullable=False, default="manual")
    ocr_confidence:    Mapped[Optional[float]]= mapped_column(Float,       nullable=True)
    validation_status: Mapped[str]            = mapped_column(String(20),  nullable=False, default="ok")
    is_personal:       Mapped[bool]           = mapped_column(Boolean,     default=False)
    is_informal:       Mapped[bool]           = mapped_column(Boolean,     default=False)
    is_flagged:        Mapped[bool]           = mapped_column(Boolean,     default=False)
    flag_reason:       Mapped[Optional[str]]  = mapped_column(Text,        nullable=True)
    created_at:        Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc),)
    updated_at:        Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class InvoiceORM(Base):
    """Maps to the invoices table."""

    __tablename__ = "invoices"

    id:          Mapped[str]               = mapped_column(String(20),  primary_key=True)
    client:      Mapped[str]               = mapped_column(String(120), nullable=False)
    description: Mapped[str]               = mapped_column(String(512), nullable=False)
    amount:      Mapped[float]             = mapped_column(Float,       nullable=False)
    date_sent:   Mapped[Optional[dateT]]    = mapped_column(Date,        nullable=True)
    date_paid:   Mapped[Optional[dateT]]    = mapped_column(Date,        nullable=True)
    status:      Mapped[str]               = mapped_column(String(20),  nullable=False, default="unpaid")
    file_id:     Mapped[Optional[str]]     = mapped_column(String(20),  ForeignKey("uploaded_files.id"), nullable=True)
    created_at:  Mapped[Optional[datetime]]= mapped_column(DateTime,    default=lambda: datetime.now(timezone.utc))


class AnomalyORM(Base):
    """Maps to the anomalies table."""

    __tablename__ = "anomalies"

    id:             Mapped[str]           = mapped_column(String(20),  primary_key=True)
    transaction_id: Mapped[str]           = mapped_column(String(20),  ForeignKey("transactions.id"), nullable=False)
    anomaly_type:   Mapped[str]           = mapped_column(String(40),  nullable=False)
    description:    Mapped[Optional[str]] = mapped_column(Text,        nullable=True)
    resolved:       Mapped[bool]          = mapped_column(Boolean,     default=False)
    detected_at:    Mapped[dateT]          = mapped_column(Date,        nullable=False)


class ActionItemORM(Base):
    """Maps to the action_items table."""

    __tablename__ = "action_items"

    id:          Mapped[str]           = mapped_column(String(20),  primary_key=True)
    text:        Mapped[str]           = mapped_column(Text,        nullable=False)
    status:      Mapped[str]           = mapped_column(String(16),  nullable=False, default="open")
    source_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at:  Mapped[dateT]          = mapped_column(Date,        nullable=False)