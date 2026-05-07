"""
Integration-style tests for the IngestionService.

Uses real repositories against the in-memory test DB,
but mocks the file storage and parsers to avoid disk I/O.
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from backend.core.enums import Category, DocType, EntryMethod, SourceType, ValidationStatus
from backend.core.models import Transaction
from backend.infrastructure.db.repositories import (
    SQLActionRepository,
    SQLFileRepository,
    SQLSourceRepository,
    SQLTransactionRepository,
)
from backend.services.ingestion_service import IngestionService


@pytest.fixture
def mock_storage():
    """Returns a mock IFileStorage that always reports success."""
    storage = MagicMock()
    storage.save.return_value = "/fake/path/receipt.png"
    storage.exists.return_value = True
    return storage


@pytest.fixture
def mock_parser():
    """Returns a mock IParser that extracts one transaction."""
    parser = MagicMock()
    parser.can_parse.return_value = True
    parser.produces_ocr = False          # ← ajouter cette ligne
    parser.parse.return_value = [
        Transaction(
            id=None,
            date=date(2025, 1, 22),
            description="Bureau en Gros",
            amount=40.80,
            category=Category.SUPPLIES,
            source_id="",
            file_id="",
            ref=None,
            entry_method=EntryMethod.OCR,
            ocr_confidence=0.92,
            validation_status=ValidationStatus.OK,
        )
    ]
    return parser


@pytest.fixture
def ingestion_service(db_session, mock_storage, mock_parser):
    """Builds a real IngestionService wired to test repositories and mock I/O."""
    return IngestionService(
        parsers=[mock_parser],
        transaction_repo=SQLTransactionRepository(db_session),
        source_repo=SQLSourceRepository(db_session),
        file_repo=SQLFileRepository(db_session),
        action_repo=SQLActionRepository(db_session),
        storage=mock_storage,
    )


def test_ingest_creates_transaction(ingestion_service, db_session):
    """A successful ingest must persist exactly one transaction in the DB."""
    result = ingestion_service.ingest(
        filename="receipt.png",
        content=b"fake image bytes",
        doc_type=DocType.RECEIPT,
        source_label="Comptant — shoebox",
        source_type=SourceType.CASH,
    )

    assert result.status == "ok"
    assert result.tx_count == 1
    assert result.total_amount == 40.80

    saved_transactions = SQLTransactionRepository(db_session).get_all()
    assert len(saved_transactions) == 1
    assert saved_transactions[0].description == "Bureau en Gros"


def test_ingest_creates_payment_source_if_missing(ingestion_service, db_session):
    """Ingesting with an unknown source label must create a new PaymentSource."""
    ingestion_service.ingest(
        filename="receipt.png",
        content=b"fake image bytes",
        doc_type=DocType.RECEIPT,
        source_label="New Card *9999",
        source_type=SourceType.CREDIT_CARD,
    )

    sources = SQLSourceRepository(db_session).get_all()
    labels  = [s.label for s in sources]
    assert "New Card *9999" in labels


def test_ingest_reuses_existing_source(ingestion_service, db_session):
    """Calling ingest twice with the same source label must not duplicate sources."""
    
    # Each call must produce a unique storage path — mimic DiskFileStorage behavior
    ingestion_service._storage.save.side_effect = [
        "/fake/path/receipt_001.png",
        "/fake/path/receipt_002.png",
    ]
    
    for _ in range(2):
        ingestion_service.ingest(
            filename="receipt.png",
            content=b"fake image bytes",
            doc_type=DocType.RECEIPT,
            source_label="Comptant — shoebox",
            source_type=SourceType.CASH,
        )

    sources  = SQLSourceRepository(db_session).get_all()
    matching = [s for s in sources if s.label == "Comptant — shoebox"]
    assert len(matching) == 1, "Same source label must not create duplicate rows."


def test_ingest_returns_no_parser_status_for_unsupported_file(db_session, mock_storage):
    """A file with no matching parser must return status='no_parser'."""
    parser_that_refuses = MagicMock()
    parser_that_refuses.can_parse.return_value = False
    parser_that_refuses.produces_ocr = False

    service = IngestionService(
        parsers=[parser_that_refuses],
        transaction_repo=SQLTransactionRepository(db_session),
        source_repo=SQLSourceRepository(db_session),
        file_repo=SQLFileRepository(db_session),
        action_repo=SQLActionRepository(db_session),
        storage=mock_storage,
    )

    result = service.ingest(
        filename="unknown.xyz",
        content=b"data",
        doc_type=DocType.RECEIPT,
        source_label="Visa *4829",
        source_type=SourceType.CREDIT_CARD,
    )

    assert result.status == "no_parser"
    assert result.tx_count == 0