"""
FastAPI Dependencies — Centralized service and session injection.

All dependencies injected into routers are defined here.
This file is the only place where FastAPI is aware of concrete 
implementations — routers only see abstract types.
"""

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.infrastructure.db.database import get_session
from backend.infrastructure.db.repositories import (
    SQLActionRepository,
    SQLAnomalyRepository,
    SQLFileRepository,
    SQLInvoiceRepository,
    SQLSourceRepository,
    SQLTransactionRepository,
)
from backend.infrastructure.parsers.image_parser import ImageReceiptParser
from backend.infrastructure.parsers.pdf_parser import PDFStatementParser
from backend.infrastructure.parsers.txt_parser import TxtNotesParser
from backend.infrastructure.parsers.xlsx_parser import XLSXParser
from backend.infrastructure.storage import DiskFileStorage
from backend.services.analytics_service import AnalyticsService
from backend.services.ingestion_service import IngestionService
from backend.services.invoice_service import InvoiceService
from backend.services.recurring_service import RecurringService
from backend.services.transaction_service import TransactionService


# Repositories 
def get_transaction_repo(
    db: Session = Depends(get_session),
) -> SQLTransactionRepository:
    """Injects the transaction repository linked to the current session."""
    return SQLTransactionRepository(db)


def get_invoice_repo(
    db: Session = Depends(get_session),
) -> SQLInvoiceRepository:
    return SQLInvoiceRepository(db)


def get_source_repo(
    db: Session = Depends(get_session),
) -> SQLSourceRepository:
    return SQLSourceRepository(db)


def get_file_repo(
    db: Session = Depends(get_session),
) -> SQLFileRepository:
    return SQLFileRepository(db)


# Services

def get_transaction_service(
    db: Session = Depends(get_session),
) -> TransactionService:
    """Injects the transaction service with its dependencies."""
    return TransactionService(
        transaction_repo=SQLTransactionRepository(db),
        anomaly_repo=SQLAnomalyRepository(db),
    )


def get_invoice_service(
    db: Session = Depends(get_session),
) -> InvoiceService:
    return InvoiceService(invoice_repo=SQLInvoiceRepository(db))


def get_ingestion_service(
    db: Session = Depends(get_session),
) -> IngestionService:
    """
    Injects the ingestion service with all its parsers.

    The order of parsers in the list determines the order in which 
    `can_parse()` is called — from most specific to most generic.
    """
    return IngestionService(
        parsers=[
            PDFStatementParser(),
            XLSXParser(),
            ImageReceiptParser(),
            TxtNotesParser(),
        ],
        transaction_repo=SQLTransactionRepository(db),
        source_repo=SQLSourceRepository(db),
        file_repo=SQLFileRepository(db),
        action_repo=SQLActionRepository(db),
        storage=DiskFileStorage(),
    )


def get_analytics_service(
    db: Session = Depends(get_session),
) -> AnalyticsService:
    return AnalyticsService(
        transaction_repo=SQLTransactionRepository(db),
        source_repo=SQLSourceRepository(db),
    )


def get_recurring_service(
    db: Session = Depends(get_session),
) -> RecurringService:
    """Injects the recurring expense detection service."""
    return RecurringService(transaction_repo=SQLTransactionRepository(db))