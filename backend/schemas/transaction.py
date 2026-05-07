"""
Pydantic schemas for transactions.

Three distinct schemas based on the segregation principle:
- TransactionCreate: data accepted during creation (POST)
- TransactionUpdate: data accepted during update (PATCH)
- TransactionRead: data returned by the API (GET)
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from backend.core.enums import (
    Category,
    EntryMethod,
    ValidationStatus,
)


class TransactionCreate(BaseModel):
    """
    Payload for creating a manual transaction.

    Used for direct entry without a source file.
    The fields ocr_confidence and file_id are not accepted
    during manual creation — they are managed by the ingestion service.
    """

    date:          date
    description:   str          = Field(min_length=1, max_length=255)
    amount:        float        = Field(description="Amount in CAD. Negative = refund.")
    category:      Category     = Category.UNCATEGORIZED
    source_id:     str          = Field(min_length=1)
    is_personal:   bool         = False
    is_informal:   bool         = False
    flag_reason:   Optional[str] = Field(default=None, max_length=512)

    @field_validator("amount")
    @classmethod
    def amount_must_not_be_zero(cls, value: float) -> float:
        """Prohibits zero amounts."""
        if value == 0.0:
            raise ValueError("Amount cannot be zero.")
        return round(value, 2)
    


class TransactionUpdate(BaseModel):
    """
    Payload for partial updates (PATCH).

    All fields are optional — only the provided fields 
    are updated (partial update pattern).
    """

    description:       Optional[str]              = Field(default=None, max_length=255)
    amount:            Optional[float]            = None
    category:          Optional[Category]         = None
    validation_status: Optional[ValidationStatus] = None
    is_personal:       Optional[bool]             = None
    is_informal:       Optional[bool]             = None
    is_flagged:        Optional[bool]             = None
    flag_reason:       Optional[str]              = Field(default=None, max_length=512)


class TransactionRead(BaseModel):
    """
    Full representation of a transaction returned by the API.

    Includes all calculated fields and traceability metadata.
    """

    id:                str
    date:              date
    description:       str
    amount:            float
    category:          Category
    source_id:         str
    file_id:           Optional[str]
    ref:               Optional[str]
    entry_method:      EntryMethod
    ocr_confidence:    Optional[float]    = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="OCR confidence between 0.0 and 1.0. Null if non-OCR.",
    )
    validation_status: ValidationStatus
    is_personal:       bool
    is_informal:       bool
    is_flagged:        bool
    flag_reason:       Optional[str]
    created_at:        datetime

    model_config = {"from_attributes": True}