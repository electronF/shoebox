"""CRUD router for issued invoices (revenue tracking)."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.api.dependencies import get_invoice_service
from backend.schemas.invoice import InvoiceCreate, InvoiceRead, InvoiceUpdate
from backend.services.invoice_service import InvoiceService

router = APIRouter()

@router.get("/", response_model=list[InvoiceRead])
def list_invoices(
    payment_status: Optional[str] = Query(default=None),
    service: InvoiceService = Depends(get_invoice_service),
) -> list[InvoiceRead]:
    """Returns all invoices, optionally filtered by payment status."""
    return service.list_invoices(status=payment_status)

@router.get("/{invoice_id}", response_model=InvoiceRead)
def get_invoice(invoice_id: str, service: InvoiceService = Depends(get_invoice_service)) -> InvoiceRead:
    """Returns a single invoice by ID."""
    invoice = service.get_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Invoice '{invoice_id}' not found.")
    return invoice

@router.post("/", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
def create_invoice(payload: InvoiceCreate, service: InvoiceService = Depends(get_invoice_service)) -> InvoiceRead:
    """Creates a new invoice."""
    return service.create(payload)

@router.patch("/{invoice_id}", response_model=InvoiceRead)
def update_invoice(invoice_id: str, payload: InvoiceUpdate, service: InvoiceService = Depends(get_invoice_service)) -> InvoiceRead:
    """Partially updates an invoice."""
    updated = service.update(invoice_id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Invoice '{invoice_id}' not found.")
    return updated