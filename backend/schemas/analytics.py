"""
Pydantic schemas for analytics and dashboard KPI endpoints.

These are read-only response models — no Create or Update variants needed.
"""

from pydantic import BaseModel, Field


class AnalyticsSummary(BaseModel):
    """
    Top-level financial summary for the dashboard overview.

    Attributes:
        total_business: Sum of all non-personal positive transaction amounts.
        total_personal: Sum of personal-flagged amounts (excluded from deductions).
        total_refunds:  Sum of absolute values of negative amounts (credits received).
        tx_count:       Total number of transactions across all sources.
        flagged_count:  Number of transactions with is_flagged=True.
    """

    total_business: float = Field(description="Total deductible business expenses in CAD.")
    total_personal: float = Field(description="Personal expenses charged to business card.")
    total_refunds:  float = Field(description="Credits and refunds received.")
    tx_count:       int   = Field(description="Total transaction count.")
    flagged_count:  int   = Field(description="Transactions requiring review.")


class CategoryBreakdown(BaseModel):
    """
    Expense total for a single category — used in list responses.

    Attributes:
        category:     Display name of the category (e.g. "Logiciels & abonnements").
        total_amount: Sum of all positive business expenses in this category.
        percentage:   Share of this category in total business expenses (0–100).
    """

    category:     str
    total_amount: float
    percentage:   float = Field(ge=0.0, le=100.0)


class MonthlyTotal(BaseModel):
    """
    Expense total for a single calendar month.

    Attributes:
        month:        ISO month string in "YYYY-MM" format (e.g. "2025-01").
        total_amount: Sum of business expenses for that month.
    """

    month:        str = Field(pattern=r"^\d{4}-\d{2}$")
    total_amount: float