"""
Detects recurring expense patterns and generates forward-looking forecasts.

A transaction is considered recurring if the same normalized merchant
appears in at least MIN_MONTHS_FOR_RECURRENCE distinct calendar months.
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field

from backend.core.enums import Category, RecurrenceFrequency
from backend.core.interfaces import ITransactionRepository
from backend.core.models import Transaction

logger = logging.getLogger(__name__)

# Minimum number of distinct months a merchant must appear in to be flagged recurring
_MIN_MONTHS_FOR_RECURRENCE = 2

# Number of future months to forecast
_FORECAST_HORIZON_MONTHS = 3

# Amount variation ratio below which a subscription is considered fixed-price
_FIXED_PRICE_VARIATION_THRESHOLD = 0.05


@dataclass
class RecurringPattern:
    """
    A detected recurring expense pattern.

    Attributes:
        merchant_key:    Normalized merchant identifier (uppercase, no punctuation).
        display_name:    Human-readable merchant name from the first seen transaction.
        frequency:       Whether the amount is fixed monthly or variable.
        avg_amount:      Average charge amount across all observed months.
        months_seen:     Sorted list of month numbers where this merchant appeared.
        category:        Expense category (from the first matched transaction).
        confidence:      Score between 0.0 and 1.0 indicating pattern reliability.
        monthly_amounts: Mapping of "YYYY-MM" to total amount charged in that month.
    """

    merchant_key:    str
    display_name:    str
    frequency:       RecurrenceFrequency
    avg_amount:      float
    months_seen:     list[int]
    category:        Category
    confidence:      float
    monthly_amounts: dict = field(default_factory=dict)


@dataclass
class ForecastEntry:
    """
    A single predicted expense for a future month.

    Attributes:
        month:         Target month in "YYYY-MM" format.
        merchant_key:  Normalized merchant identifier.
        display_name:  Human-readable merchant name.
        predicted_amt: Expected charge amount.
        confidence:    Confidence score inherited from the source pattern.
        is_fixed:      True if the amount is expected to be consistent.
    """

    month:         str
    merchant_key:  str
    display_name:  str
    predicted_amt: float
    confidence:    float
    is_fixed:      bool


class RecurringService:
    """
    Analyses transaction history to identify recurring charges
    and project them into future months.

    Args:
        transaction_repo: Repository providing transaction data.
    """

    def __init__(self, transaction_repo: ITransactionRepository) -> None:
        self._transaction_repo = transaction_repo

    def detect_patterns(self) -> list[RecurringPattern]:
        """
        Scans all non-personal positive transactions for recurring merchants.

        Returns:
            List of RecurringPattern objects sorted by average amount descending.
        """
        transactions = self._transaction_repo.get_all(exclude_personal=True)
        positive_transactions = [t for t in transactions if t.amount > 0]

        # Group transactions by normalized merchant key
        by_merchant: dict[str, list[Transaction]] = defaultdict(list)
        for transaction in positive_transactions:
            key = _normalize_merchant(transaction.description)
            by_merchant[key].append(transaction)

        patterns: list[RecurringPattern] = []

        for merchant_key, merchant_transactions in by_merchant.items():
            distinct_months = sorted({t.date.month for t in merchant_transactions})

            if len(distinct_months) < _MIN_MONTHS_FOR_RECURRENCE:
                continue

            amounts   = [t.amount for t in merchant_transactions]
            avg       = sum(amounts) / len(amounts)
            variation = (max(amounts) - min(amounts)) / avg if avg > 0 else 0.0

            frequency = (
                RecurrenceFrequency.MONTHLY
                if variation < _FIXED_PRICE_VARIATION_THRESHOLD
                else RecurrenceFrequency.VARIABLE
            )

            # Confidence: higher when seen more months and variation is low
            confidence = min(
                1.0,
                (len(distinct_months) / 3.0) * (1.0 - variation * 0.5),
            )

            monthly_amounts: dict[str, float] = {}
            for t in merchant_transactions:
                key = t.date.strftime("%Y-%m")
                monthly_amounts[key] = round(monthly_amounts.get(key, 0) + t.amount, 2)

            patterns.append(RecurringPattern(
                merchant_key=merchant_key,
                display_name=merchant_transactions[0].description,
                frequency=frequency,
                avg_amount=round(avg, 2),
                months_seen=distinct_months,
                category=merchant_transactions[0].category,
                confidence=round(confidence, 2),
                monthly_amounts=monthly_amounts,
            ))

            logger.debug(
                "Recurring pattern: '%s' avg=$%.2f months=%s confidence=%.0f%%",
                merchant_key, avg, distinct_months, confidence * 100,
            )

        return sorted(patterns, key=lambda p: p.avg_amount, reverse=True)

    def forecast(
        self,
        patterns:   list[RecurringPattern],
        last_month: int,
        year:       int,
    ) -> list[ForecastEntry]:
        """
        Projects detected patterns forward for FORECAST_HORIZON_MONTHS months.

        Args:
            patterns:   List of RecurringPattern objects to project.
            last_month: The last observed month number (e.g. 3 for March).
            year:       The year of the last observed month.

        Returns:
            List of ForecastEntry objects, one per pattern per future month,
            sorted chronologically.
        """
        entries: list[ForecastEntry] = []

        for pattern in patterns:
            for offset in range(1, _FORECAST_HORIZON_MONTHS + 1):
                # Compute the target month, wrapping across year boundaries
                raw_month    = last_month + offset
                target_month = (raw_month - 1) % 12 + 1
                target_year  = year + (raw_month - 1) // 12
                month_str    = f"{target_year}-{target_month:02d}"

                entries.append(ForecastEntry(
                    month=month_str,
                    merchant_key=pattern.merchant_key,
                    display_name=pattern.display_name,
                    predicted_amt=pattern.avg_amount,
                    confidence=pattern.confidence,
                    is_fixed=pattern.frequency == RecurrenceFrequency.MONTHLY,
                ))

        return sorted(entries, key=lambda e: e.month)


# Module-level helper
def _normalize_merchant(description: str) -> str:
    """
    Produces a stable key from a merchant description for grouping purposes.

    Removes non-alphanumeric characters and truncates to 20 characters.

    Args:
        description: Raw transaction description.

    Returns:
        Normalized uppercase string (e.g. "GOOGLEWORKSPACE").

    Example::

        _normalize_merchant("GOOGLE *WORKSPACE")  # → "GOOGLEWORKSPACE"
        _normalize_merchant("Shopify* 1234567")    # → "SHOPIFY1234567"
    """
    return re.sub(r"[^A-Z0-9]", "", description.upper())[:20]