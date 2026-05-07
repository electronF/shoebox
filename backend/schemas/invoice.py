"""Pydantic schemas for issued invoices (income)."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from backend.core.enums import InvoiceStatus


class InvoiceCreate(BaseModel):
    """Payload for creating an issued invoice."""

    client:      str           = Field(min_length=1, max_length=120)
    description: str           = Field(min_length=1, max_length=512)
    amount:      float         = Field(gt=0, description="Amount (before tax) in CAD.")
    date_sent:   Optional[date] = None
    date_paid:   Optional[date] = None
    status:      InvoiceStatus  = InvoiceStatus.UNPAID

    @model_validator(mode="after")
    def paid_date_requires_paid_status(self) -> "InvoiceCreate":
        """
        Consistency check: a payment date implies a 'paid' status.
        """
        if self.date_paid and self.status != InvoiceStatus.PAID:
            raise ValueError(
                "date_paid can only be provided if status='paid'."
            )
        return self


class InvoiceUpdate(BaseModel):
    """Payload for partial invoice update."""

    client:      Optional[str]           = None
    description: Optional[str]           = None
    amount:      Optional[float]         = Field(default=None, gt=0)
    date_sent:   Optional[date]          = None
    date_paid:   Optional[date]          = None
    status:      Optional[InvoiceStatus] = None


class InvoiceRead(BaseModel):
    """Full representation of an invoice returned by the API."""

    id:          str
    client:      str
    description: str
    amount:      float
    date_sent:   Optional[date]
    date_paid:   Optional[date]
    status:      InvoiceStatus
    file_id:     Optional[str]
    created_at:  datetime

    model_config = {"from_attributes": True}