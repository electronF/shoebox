from sqlalchemy import (
    Column, String, Float, Boolean, Date,
    Integer, ForeignKey, Text, DateTime, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
from ...core.enums import (
    Category, SourceType, FileType,
    RecurrenceFrequency, EntryMethod, ValidationStatus
)

class DocumentTypeORM(Base):
    """
    Catalog of supported document types.
    Drives the upload popup and format validation.
    """
    __tablename__ = "document_types"

    id            = Column(String(8),   primary_key=True)  # e.g.: "REC", "STMT", "INV"
    label         = Column(String(120), nullable=False)
    accepted_fmts = Column(String(64),  nullable=False)    # "jpg,png,pdf"
    multi_file    = Column(Boolean,     default=True)
    single_source = Column(Boolean,     default=False)     # statement = True
    schema_json   = Column(Text)        # JSON of expected fields + rules


class PaymentSourceORM(Base):
    """
    One entry per card or payment source.
    Automatically created during ingestion if new.
    """
    __tablename__ = "payment_sources"

    id          = Column(String(20),  primary_key=True)   # Meaningful ID: SRC-240601-00001
    label       = Column(String(120), nullable=False, unique=True)
    source_type = Column(SAEnum(SourceType), nullable=False)
    last_four   = Column(String(4))
    created_at  = Column(Date, nullable=False)


class UploadedFileORM(Base):
    """
    Tracks every ingested file — link between physical file and transactions.
    """
    __tablename__ = "uploaded_files"

    id              = Column(String(20),  primary_key=True)  # e.g.: REC-240122-00001
    filename        = Column(String(255), nullable=False)
    file_type       = Column(SAEnum(FileType), nullable=False)
    doc_type_id     = Column(String(8),   ForeignKey("document_types.id"))
    storage_path    = Column(String(512), nullable=False, unique=True)
    source_id       = Column(String(20),  ForeignKey("payment_sources.id"))
    uploaded_at     = Column(Date,        nullable=False)
    tx_count        = Column(Integer,     default=0)
    total_amount    = Column(Float,       default=0.0)
    ocr_attempted   = Column(Boolean,     default=False)
    ocr_success     = Column(Boolean,     default=False)


class TransactionORM(Base):
    """
    Core of the system. Each row = one expense or income.
    entry_method tracks how the row was created.
    """
    __tablename__ = "transactions"

    id              = Column(String(20),  primary_key=True)  # e.g.: REC-240122-00001
    date            = Column(Date,        nullable=False)
    description     = Column(String(255), nullable=False)
    amount          = Column(Float,       nullable=False)
    category        = Column(SAEnum(Category), nullable=False,
                             default=Category.UNCATEGORIZED)
    source_id       = Column(String(20),  ForeignKey("payment_sources.id"), nullable=False)
    file_id         = Column(String(20),  ForeignKey("uploaded_files.id"))
    ref             = Column(String(64))

    # Data entry traceability
    entry_method    = Column(SAEnum(EntryMethod), nullable=False,
                             default=EntryMethod.MANUAL)
    ocr_confidence  = Column(Float)         # None if entry_method != 'ocr'
    validation_status = Column(SAEnum(ValidationStatus),
                               default=ValidationStatus.PENDING)

    # Business flags
    is_personal     = Column(Boolean, default=False)
    is_informal     = Column(Boolean, default=False)   # handwritten receipt without taxes
    is_flagged      = Column(Boolean, default=False)
    flag_reason     = Column(Text)

    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow,
                             onupdate=datetime.utcnow)


class RecurringPatternORM(Base):
    __tablename__ = "recurring_patterns"

    id           = Column(String(20),  primary_key=True)
    merchant_key = Column(String(120), nullable=False, unique=True)
    display_name = Column(String(120), nullable=False)
    frequency    = Column(SAEnum(RecurrenceFrequency), nullable=False)
    avg_amount   = Column(Float,       nullable=False)
    months_seen  = Column(String(32))   # "1,2,3"
    category     = Column(SAEnum(Category), nullable=False)
    confidence   = Column(Float, default=0.0)


class ForecastORM(Base):
    __tablename__ = "forecasts"

    id            = Column(String(20), primary_key=True)
    month         = Column(String(7),  nullable=False)   # "2025-04"
    merchant_key  = Column(String(120),nullable=False)
    predicted_amt = Column(Float,      nullable=False)
    confidence    = Column(Float,      nullable=False)
    is_fixed      = Column(Boolean,    default=False)
    pattern_id    = Column(String(20), ForeignKey("recurring_patterns.id"))


class AnomalyORM(Base):
    __tablename__ = "anomalies"

    id             = Column(String(20), primary_key=True)
    transaction_id = Column(String(20), ForeignKey("transactions.id"))
    anomaly_type   = Column(String(64), nullable=False)  # "duplicate", "personal_on_biz", "tax_mismatch"
    description    = Column(Text)
    resolved       = Column(Boolean,    default=False)
    detected_at    = Column(Date,       nullable=False)


class ActionItemORM(Base):
    """Tasks extracted from notes.txt ([todo] / [done])"""
    __tablename__ = "action_items"

    id          = Column(String(20),  primary_key=True)
    text        = Column(Text,        nullable=False)
    status      = Column(String(16),  default="open")   # "open" | "done"
    source_file = Column(String(255))
    created_at  = Column(Date,        nullable=False)