"""
Concrete SQL implementations of the repository interfaces defined in core/interfaces.py.

Each repository class:
- Accepts a SQLAlchemy Session in its constructor (injected by FastAPI Depends)
- Converts between ORM models and domain dataclasses
- Never leaks ORM objects outside this module
"""

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from backend.core.enums import (
    AnomalyType,
    Category,
    DocType,
    EntryMethod,
    FileType,
    InvoiceStatus,
    SourceType,
    ValidationStatus,
)
from backend.core.interfaces import (
    IAnomalyRepository,
    IActionRepository,
    IFileRepository,
    IInvoiceRepository,
    ISourceRepository,
    ITransactionRepository,
)
from backend.core.models import (
    ActionItem,
    Anomaly,
    Invoice,
    PaymentSource,
    Transaction,
    UploadedFile,
)
from backend.infrastructure.db.id_generator import generate_id
from backend.infrastructure.db.orm_models import (
    ActionItemORM,
    AnomalyORM,
    InvoiceORM,
    PaymentSourceORM,
    TransactionORM,
    UploadedFileORM,
)


class SQLTransactionRepository(ITransactionRepository):
    """
    SQLAlchemy-backed transaction repository.

    Args:
        session: Active SQLAlchemy session for the current request.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # Private helpers
    @staticmethod
    def _to_domain(orm: TransactionORM) -> Transaction:
        """Converts a TransactionORM row to a Transaction domain object."""
        return Transaction(
            id=orm.id,
            date=orm.date,
            description=orm.description,
            amount=orm.amount,
            category=Category(orm.category),
            source_id=orm.source_id,
            file_id=orm.file_id,
            ref=orm.ref,
            entry_method=EntryMethod(orm.entry_method),
            ocr_confidence=orm.ocr_confidence,
            validation_status=ValidationStatus(orm.validation_status),
            is_personal=orm.is_personal,
            is_informal=orm.is_informal,
            is_flagged=orm.is_flagged,
            flag_reason=orm.flag_reason,
            created_at=orm.created_at or datetime.utcnow(),
        )

    # Interface implementation
    def save(self, transaction: Transaction) -> Transaction:

        """
        Persists a new transaction and returns it with a generated ID.

        Args:
            transaction: Domain object to persist. Its id field must be None.

        Returns:
            The same transaction with id populated.
        """
        transaction.id = generate_id(
            self._session,
            "transactions",
            doc_type=None,
        )
        orm = TransactionORM(
            id=transaction.id,
            date=transaction.date,
            description=transaction.description,
            amount=transaction.amount,
            category=transaction.category.value,
            source_id=transaction.source_id,
            file_id=transaction.file_id,
            ref=transaction.ref,
            entry_method=transaction.entry_method.value,
            ocr_confidence=transaction.ocr_confidence,
            validation_status=transaction.validation_status.value,
            is_personal=transaction.is_personal,
            is_informal=transaction.is_informal,
            is_flagged=transaction.is_flagged,
            flag_reason=transaction.flag_reason,
        )
        self._session.add(orm)
        self._session.commit()
        return transaction

    def get_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """Returns a transaction by ID, or None if not found."""
        orm = self._session.get(TransactionORM, transaction_id)
        return self._to_domain(orm) if orm else None

    def get_all(
        self,
        source_id: Optional[str] = None,
        exclude_personal: bool = False,
    ) -> list[Transaction]:
        """
        Returns transactions with optional filters.

        Args:
            source_id:        Filter by payment source ID if provided.
            exclude_personal: When True, omits personal-flagged transactions.

        Returns:
            List of Transaction domain objects ordered by date ascending.
        """
        query = self._session.query(TransactionORM)

        if source_id:
            query = query.filter(TransactionORM.source_id == source_id)
        if exclude_personal:
            query = query.filter(TransactionORM.is_personal == False)  # noqa: E712

        rows = query.order_by(TransactionORM.date).all()
        return [self._to_domain(row) for row in rows]

    def get_by_file(self, file_id: str) -> list[Transaction]:
        """Returns all transactions extracted from a given file."""
        rows = (
            self._session.query(TransactionORM)
            .filter(TransactionORM.file_id == file_id)
            .all()
        )
        return [self._to_domain(row) for row in rows]

    def update(self, transaction: Transaction) -> Transaction:
        """
        Updates an existing transaction in place.

        Args:
            transaction: Domain object with updated fields and a valid ID.

        Returns:
            The updated transaction.
        """
        orm = self._session.get(TransactionORM, transaction.id)
        if not orm:
            raise ValueError(f"Transaction '{transaction.id}' not found.")

        orm.description       = transaction.description
        orm.amount            = transaction.amount
        orm.category          = transaction.category.value
        orm.validation_status = transaction.validation_status.value
        orm.is_personal       = transaction.is_personal
        orm.is_informal       = transaction.is_informal
        orm.is_flagged        = transaction.is_flagged
        orm.flag_reason       = transaction.flag_reason
        orm.updated_at        = datetime.now(timezone.utc)

        self._session.commit()
        return transaction

    def delete(self, transaction_id: str) -> bool:
        """
        Deletes a transaction by ID.

        Returns:
            True if the transaction existed and was deleted, False otherwise.
        """
        orm = self._session.get(TransactionORM, transaction_id)
        if not orm:
            return False
        self._session.delete(orm)
        self._session.commit()
        return True


class SQLInvoiceRepository(IInvoiceRepository):
    """SQLAlchemy-backed invoice repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(orm: InvoiceORM) -> Invoice:
        """Converts an InvoiceORM row to an Invoice domain object."""
        return Invoice(
            id=orm.id,
            client=orm.client,
            description=orm.description,
            amount=orm.amount,
            date_sent=orm.date_sent,
            date_paid=orm.date_paid,
            status=InvoiceStatus(orm.status),
            file_id=orm.file_id,
            created_at=orm.created_at or datetime.utcnow(),
        )

    def save(self, invoice: Invoice) -> Invoice:
        """Persists a new invoice and returns it with a generated ID."""
        invoice.id = generate_id(self._session, "invoices")
        orm = InvoiceORM(
            id=invoice.id,
            client=invoice.client,
            description=invoice.description,
            amount=invoice.amount,
            date_sent=invoice.date_sent,
            date_paid=invoice.date_paid,
            status=invoice.status.value,
            file_id=invoice.file_id,
        )
        self._session.add(orm)
        self._session.commit()
        return invoice

    def get_by_id(self, invoice_id: str) -> Optional[Invoice]:
        """Returns an invoice by ID, or None if not found."""
        orm = self._session.get(InvoiceORM, invoice_id)
        return self._to_domain(orm) if orm else None

    def get_all(self, status: Optional[str] = None) -> list[Invoice]:
        """
        Returns all invoices, optionally filtered by payment status.

        Args:
            status: One of "paid", "unpaid", "overdue", "void". Optional.
        """
        query = self._session.query(InvoiceORM)
        if status:
            query = query.filter(InvoiceORM.status == status)
        return [self._to_domain(row) for row in query.order_by(InvoiceORM.date_sent).all()]

    def update(self, invoice: Invoice) -> Invoice:
        """Updates an existing invoice."""
        orm = self._session.get(InvoiceORM, invoice.id)
        if not orm:
            raise ValueError(f"Invoice '{invoice.id}' not found.")
        orm.client      = invoice.client
        orm.description = invoice.description
        orm.amount      = invoice.amount
        orm.date_sent   = invoice.date_sent
        orm.date_paid   = invoice.date_paid
        orm.status      = invoice.status.value
        self._session.commit()
        return invoice


class SQLSourceRepository(ISourceRepository):
    """SQLAlchemy-backed payment source repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(orm: PaymentSourceORM) -> PaymentSource:
        return PaymentSource(
            id=orm.id,
            label=orm.label,
            source_type=SourceType(orm.source_type),
            last_four=orm.last_four,
            created_at=orm.created_at,
        )

    def save(self, source: PaymentSource) -> PaymentSource:
        """Persists a new payment source."""
        source.id = generate_id(self._session, "payment_sources")
        orm = PaymentSourceORM(
            id=source.id,
            label=source.label,
            source_type=source.source_type.value,
            last_four=source.last_four,
            created_at=source.created_at,
        )
        self._session.add(orm)
        self._session.commit()
        return source

    def get_all(self) -> list[PaymentSource]:
        """Returns all payment sources."""
        rows = self._session.query(PaymentSourceORM).all()
        return [self._to_domain(row) for row in rows]

    def find_by_label(self, label: str) -> Optional[PaymentSource]:
        """Returns the source matching the given label, or None."""
        orm = (
            self._session.query(PaymentSourceORM)
            .filter(PaymentSourceORM.label == label)
            .first()
        )
        return self._to_domain(orm) if orm else None
    
    def find_by_id(self, source_id: str) -> Optional[PaymentSource]:
        """Returns the source matching the given ID, or None."""
        orm = self._session.get(PaymentSourceORM, source_id)
        return self._to_domain(orm) if orm else None


class SQLFileRepository(IFileRepository):
    """SQLAlchemy-backed uploaded file repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(orm: UploadedFileORM) -> UploadedFile:
        return UploadedFile(
            id=orm.id,
            filename=orm.filename,
            file_type=FileType(orm.file_type),
            doc_type=DocType(orm.doc_type),
            storage_path=orm.storage_path,
            source_id=orm.source_id,
            uploaded_at=orm.uploaded_at,
            tx_count=orm.tx_count,
            total_amount=orm.total_amount,
            ocr_attempted=orm.ocr_attempted,
            ocr_success=orm.ocr_success,
        )

    def save(self, uploaded_file: UploadedFile) -> UploadedFile:
        """Persists a new uploaded file record."""
        uploaded_file.id = generate_id(
            self._session,
            "uploaded_files",
            doc_type=uploaded_file.doc_type,
        )
        orm = UploadedFileORM(
            id=uploaded_file.id,
            filename=uploaded_file.filename,
            file_type=uploaded_file.file_type.value,
            doc_type=uploaded_file.doc_type.value,
            storage_path=uploaded_file.storage_path,
            source_id=uploaded_file.source_id,
            uploaded_at=uploaded_file.uploaded_at,
            ocr_attempted=uploaded_file.ocr_attempted,
            ocr_success=uploaded_file.ocr_success,
        )
        self._session.add(orm)
        self._session.commit()
        return uploaded_file

    def get_all(self) -> list[UploadedFile]:
        """Returns all uploaded file records ordered by upload date descending."""
        rows = (
            self._session.query(UploadedFileORM)
            .order_by(UploadedFileORM.uploaded_at.desc())
            .all()
        )
        return [self._to_domain(row) for row in rows]

    def update_stats(
        self,
        file_id: str,
        tx_count: int,
        total_amount: float,
    ) -> None:
        """
        Updates the aggregated statistics for a file after ingestion completes.

        Args:
            file_id:      ID of the uploaded file to update.
            tx_count:     Number of transactions extracted from this file.
            total_amount: Sum of all positive transaction amounts.
        """
        self._session.query(UploadedFileORM).filter(
            UploadedFileORM.id == file_id
        ).update({"tx_count": tx_count, "total_amount": total_amount})
        self._session.commit()

    def update_ocr_status(
        self,
        file_id:      str,
        ocr_attempted: bool,
        ocr_success:   bool,
    ) -> None:
        """Updates the OCR status flags after ingestion completes."""
        self._session.query(UploadedFileORM).filter(
            UploadedFileORM.id == file_id
        ).update({
            "ocr_attempted": ocr_attempted,
            "ocr_success":   ocr_success,
        })
        self._session.commit()

class SQLAnomalyRepository(IAnomalyRepository):
    """SQLAlchemy-backed anomaly repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(orm: AnomalyORM) -> Anomaly:
        return Anomaly(
            id=orm.id,
            transaction_id=orm.transaction_id,
            anomaly_type=AnomalyType(orm.anomaly_type),
            description=orm.description or "",
            resolved=orm.resolved,
            detected_at=orm.detected_at,
        )

    def save(self, anomaly: Anomaly) -> Anomaly:
        """Persists a detected anomaly."""
        anomaly.id = generate_id(self._session, "anomalies")
        orm = AnomalyORM(
            id=anomaly.id,
            transaction_id=anomaly.transaction_id,
            anomaly_type=anomaly.anomaly_type.value,
            description=anomaly.description,
            resolved=anomaly.resolved,
            detected_at=anomaly.detected_at,
        )
        self._session.add(orm)
        self._session.commit()
        return anomaly

    def get_unresolved(self) -> list[Anomaly]:
        """Returns all unresolved anomalies."""
        rows = (
            self._session.query(AnomalyORM)
            .filter(AnomalyORM.resolved == False)  # noqa: E712
            .all()
        )
        return [self._to_domain(row) for row in rows]

    def mark_resolved(self, anomaly_id: str) -> bool:
        """
        Marks an anomaly as resolved.

        Returns:
            True if found and updated, False otherwise.
        """
        updated = (
            self._session.query(AnomalyORM)
            .filter(AnomalyORM.id == anomaly_id)
            .update({"resolved": True})
        )
        self._session.commit()
        return updated > 0


class SQLActionRepository(IActionRepository):
    """SQLAlchemy-backed action item repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(orm: ActionItemORM) -> ActionItem:
        return ActionItem(
            id=orm.id,
            text=orm.text,
            status=orm.status,
            source_file=orm.source_file,
            created_at=orm.created_at,
        )

    def save(self, action: ActionItem) -> ActionItem:
        """Persists a new action item."""
        action.id = generate_id(self._session, "action_items")
        orm = ActionItemORM(
            id=action.id,
            text=action.text,
            status=action.status,
            source_file=action.source_file,
            created_at=action.created_at,
        )
        self._session.add(orm)
        self._session.commit()
        return action

    def get_all(self, status: Optional[str] = None) -> list[ActionItem]:
        """Returns all action items, optionally filtered by status."""
        query = self._session.query(ActionItemORM)
        if status:
            query = query.filter(ActionItemORM.status == status)
        return [self._to_domain(row) for row in query.order_by(ActionItemORM.created_at).all()]

    def update_status(self, action_id: str, status: str) -> bool:
        """Updates the status of an action item. Returns True if found."""
        updated = (
            self._session.query(ActionItemORM)
            .filter(ActionItemORM.id == action_id)
            .update({"status": status})
        )
        self._session.commit()
        return updated > 0