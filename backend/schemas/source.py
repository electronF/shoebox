"""
Pydantic schemas for payment sources.

PaymentSourceCreate is used when a new source is declared at upload time.
PaymentSourceRead is returned by the API for any source-related response.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from backend.core.enums import SourceType


class PaymentSourceCreate(BaseModel):
    """
    Payload for registering a new payment source.

    Attributes:
        label:       Human-readable name shown in the UI (e.g. "Visa *4829").
        source_type: Category of the source (credit card, cash, personal).
        last_four:   Last 4 digits of the card number, if applicable.
    """

    label:       str        = Field(min_length=1, max_length=120)
    source_type: SourceType
    last_four:   Optional[str] = Field(default=None, min_length=4, max_length=4)


class PaymentSourceRead(BaseModel):
    """
    Full payment source representation returned by the API.

    Attributes:
        id:          Generated ID (e.g. "SRC-250101-00001").
        label:       Human-readable label.
        source_type: Type of source.
        last_four:   Last 4 card digits, or None for cash/personal sources.
        created_at:  Date the source was first registered.
    """

    id:          str
    label:       str
    source_type: SourceType
    last_four:   Optional[str]
    created_at:  date

    model_config = {"from_attributes": True}