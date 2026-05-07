"""Business logic for issued invoice management (revenue tracking)."""

import logging
from datetime import date
from typing import Optional

from backend.core.interfaces import IInvoiceRepository
from backend.core.models import Invoice
from backend.schemas.invoice import InvoiceCreate, InvoiceRead, InvoiceUpdate

logger = logging.getLogger(__name__)


class InvoiceService:
    """
    Manages creation, retrieval and updates of issued invoices.

    Args:
        invoice_repo: Repository for invoice persistence.
    """

    def __init__(self, invoice_repo: IInvoiceRepository) -> None:
        self._invoice_repo = invoice_repo

    def list_invoices(self, status: Optional[str] = None) -> list[InvoiceRead]:
        """
        Returns all invoices, optionally filtered by payment status.

        Args:
            status: "paid", "unpaid", "overdue", or "void". Optional.
        """
        invoices = self._invoice_repo.get_all(status=status)
        return [self._to_read_schema(inv) for inv in invoices]

    def get_by_id(self, invoice_id: str) -> Optional[InvoiceRead]:
        """Returns a single invoice by ID, or None if not found."""
        invoice = self._invoice_repo.get_by_id(invoice_id)
        return self._to_read_schema(invoice) if invoice else None

    def create(self, payload: InvoiceCreate) -> InvoiceRead:
        """
        Creates a new invoice from a validated Pydantic payload.

        Args:
            payload: Validated InvoiceCreate schema.

        Returns:
            The persisted invoice as InvoiceRead.
        """
        invoice = Invoice(
            id=None,
            client=payload.client,
            description=payload.description,
            amount=round(payload.amount, 2),
            date_sent=payload.date_sent,
            date_paid=payload.date_paid,
            status=payload.status,
            file_id=None,
        )
        saved = self._invoice_repo.save(invoice)
        logger.info("Invoice created: %s — %s ($%.2f)", saved.id, saved.client, saved.amount)
        return self._to_read_schema(saved)

    def update(self, invoice_id: str, payload: InvoiceUpdate) -> Optional[InvoiceRead]:
        """
        Partially updates an invoice.

        Args:
            invoice_id: ID of the invoice to update.
            payload:    Fields to update (all optional).

        Returns:
            Updated InvoiceRead, or None if not found.
        """
        existing = self._invoice_repo.get_by_id(invoice_id)
        if not existing:
            return None

        if payload.client      is not None: existing.client      = payload.client
        if payload.description is not None: existing.description = payload.description
        if payload.amount      is not None: existing.amount      = round(payload.amount, 2)
        if payload.date_sent   is not None: existing.date_sent   = payload.date_sent
        if payload.date_paid   is not None: existing.date_paid   = payload.date_paid
        if payload.status      is not None: existing.status      = payload.status

        updated = self._invoice_repo.update(existing)
        return self._to_read_schema(updated)

    @staticmethod
    def _to_read_schema(invoice: Invoice) -> InvoiceRead:
        """Converts an Invoice domain object to an InvoiceRead Pydantic schema."""
        return InvoiceRead(
            id=invoice.id if invoice.id != None else "",
            client=invoice.client,
            description=invoice.description,
            amount=invoice.amount,
            date_sent=invoice.date_sent,
            date_paid=invoice.date_paid,
            status=invoice.status,
            file_id=invoice.file_id,
            created_at=invoice.created_at,
        )