"""
Business logic for transaction management.

Handles CRUD operations and enforces domain rules such as
automatic anomaly detection on creation.
"""

import logging
from datetime import date
from typing import Optional

from backend.core.enums import (
    AnomalyType,
    Category,
    EntryMethod,
    ValidationStatus,
)
from backend.core.interfaces import IAnomalyRepository, ITransactionRepository
from backend.core.models import Anomaly, Transaction
from backend.schemas.transaction import TransactionCreate, TransactionRead, TransactionUpdate

logger = logging.getLogger(__name__)


class TransactionService:
    """
    Manages transaction creation, retrieval, update, and deletion.

    Also triggers anomaly detection when transactions are persisted.

    Args:
        transaction_repo: Repository for transaction persistence.
        anomaly_repo:     Repository for anomaly persistence.
    """

    def __init__(
        self,
        transaction_repo: ITransactionRepository,
        anomaly_repo:     IAnomalyRepository,
    ) -> None:
        self._transaction_repo = transaction_repo
        self._anomaly_repo     = anomaly_repo

    def list_transactions(
        self,
        source_id:        Optional[str]      = None,
        category:         Optional[Category] = None,
        exclude_personal: bool               = False,
        page:             int                = 1,
        size:             int                = 50,
    ) -> tuple[list[TransactionRead], int]:
        """
        Returns a paginated list of transactions with optional filters.

        Args:
            source_id:        Filter by payment source ID.
            category:         Filter by expense category.
            exclude_personal: Exclude personal transactions when True.
            page:             Page number (1-indexed).
            size:             Items per page.

        Returns:
            Tuple of (page items, total count).
        """
        all_transactions = self._transaction_repo.get_all(
            source_id=source_id,
            exclude_personal=exclude_personal,
        )

        if category:
            all_transactions = [
                t for t in all_transactions if t.category == category
            ]

        total  = len(all_transactions)
        offset = (page - 1) * size
        page_items = all_transactions[offset : offset + size]

        return [self._to_read_schema(t) for t in page_items], total

    def get_by_id(self, transaction_id: str) -> Optional[TransactionRead]:
        """
        Returns a transaction by its ID.

        Args:
            transaction_id: Unique transaction identifier.

        Returns:
            TransactionRead schema, or None if not found.
        """
        transaction = self._transaction_repo.get_by_id(transaction_id)
        return self._to_read_schema(transaction) if transaction else None

    def create_manual(self, payload: TransactionCreate) -> TransactionRead:
        """
        Creates a manually entered transaction (no file source).

        Args:
            payload: Validated Pydantic schema from the API layer.

        Returns:
            The persisted transaction as a read schema.
        """
        transaction = Transaction(
            id=None,
            date=payload.date,
            description=payload.description,
            amount=round(payload.amount, 2),
            category=payload.category,
            source_id=payload.source_id,
            file_id=None,
            ref=None,
            entry_method=EntryMethod.MANUAL,
            ocr_confidence=None,
            validation_status=ValidationStatus.OK,
            is_personal=payload.is_personal,
            is_informal=payload.is_informal,
            is_flagged=False,
            flag_reason=payload.flag_reason,
        )

        saved = self._transaction_repo.save(transaction)
        self._detect_anomalies(saved)

        logger.info("Manual transaction created: %s — %s", saved.id, saved.description)
        return self._to_read_schema(saved)

    def update(
        self, transaction_id: str, payload: TransactionUpdate
    ) -> Optional[TransactionRead]:
        """
        Partially updates a transaction.

        Only fields explicitly provided in the payload are updated.

        Args:
            transaction_id: ID of the transaction to update.
            payload:        Pydantic schema with optional fields.

        Returns:
            Updated TransactionRead, or None if not found.
        """
        existing = self._transaction_repo.get_by_id(transaction_id)
        if not existing:
            return None

        # Apply only the fields that were provided
        if payload.description is not None:
            existing.description = payload.description
        if payload.amount is not None:
            existing.amount = round(payload.amount, 2)
        if payload.category is not None:
            existing.category = payload.category
        if payload.validation_status is not None:
            existing.validation_status = payload.validation_status
        if payload.is_personal is not None:
            existing.is_personal = payload.is_personal
        if payload.is_informal is not None:
            existing.is_informal = payload.is_informal
        if payload.is_flagged is not None:
            existing.is_flagged = payload.is_flagged
        if payload.flag_reason is not None:
            existing.flag_reason = payload.flag_reason

        updated = self._transaction_repo.update(existing)
        return self._to_read_schema(updated)

    def delete(self, transaction_id: str) -> bool:
        """
        Deletes a transaction by ID.

        Returns:
            True if found and deleted, False otherwise.
        """
        return self._transaction_repo.delete(transaction_id)

    # ── Private helpers 

    def _detect_anomalies(self, transaction: Transaction) -> None:
        """
        Checks a newly saved transaction for known anomaly patterns
        and persists any detected anomalies.

        Current rules:
        - Personal expense on a business card (is_personal=True, source not personal).
        """
        if transaction.is_personal:
            self._anomaly_repo.save(Anomaly(
                id=None,
                transaction_id=transaction.id if transaction.id != None else "",
                anomaly_type=AnomalyType.PERSONAL_ON_BIZ,
                description=(
                    f"Personal expense on business card: '{transaction.description}'"
                ),
                resolved=False,
                detected_at=date.today(),
            ))

    @staticmethod
    def _to_read_schema(transaction: Transaction) -> TransactionRead:
        """Converts a Transaction domain object to a TransactionRead Pydantic schema."""
        return TransactionRead(
            id=transaction.id if transaction.id != None else "",
            date=transaction.date,
            description=transaction.description,
            amount=transaction.amount,
            category=transaction.category,
            source_id=transaction.source_id,
            file_id=transaction.file_id,
            ref=transaction.ref,
            entry_method=transaction.entry_method,
            ocr_confidence=transaction.ocr_confidence,
            validation_status=transaction.validation_status,
            is_personal=transaction.is_personal,
            is_informal=transaction.is_informal,
            is_flagged=transaction.is_flagged,
            flag_reason=transaction.flag_reason,
            created_at=transaction.created_at,
        )