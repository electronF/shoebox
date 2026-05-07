"""
Computes KPIs and aggregated statistics for the dashboard.

Read-only service — never modifies data.
All computation happens in Python after fetching from the repository
to avoid complex SQL queries and keep the logic testable.
"""

import logging
from collections import defaultdict
from typing import Optional

from pydantic import BaseModel

from backend.core.interfaces import ISourceRepository, ITransactionRepository

logger = logging.getLogger(__name__)


class AnalyticsSummary(BaseModel):
    """Top-level financial summary returned by GET /analytics/summary."""

    total_business:  float  # sum of non-personal positive amounts
    total_personal:  float  # sum of personal positive amounts (to exclude)
    total_refunds:   float  # sum of absolute negative amounts (credits received)
    tx_count:        int
    flagged_count:   int


class AnalyticsService:
    """
    Computes aggregated financial metrics from transaction data.

    Args:
        transaction_repo: Repository providing transaction data.
        source_repo:      Repository providing source labels for grouping.
    """

    def __init__(
        self,
        transaction_repo: ITransactionRepository,
        source_repo:      ISourceRepository,
    ) -> None:
        self._transaction_repo = transaction_repo
        self._source_repo      = source_repo

    def compute_summary(self) -> AnalyticsSummary:
        """
        Computes the top-level financial summary across all transactions.

        Returns:
            AnalyticsSummary with totals for business expenses, personal
            expenses, refunds, total transaction count, and flagged count.
        """
        all_transactions = self._transaction_repo.get_all()

        business_transactions  = [t for t in all_transactions if not t.is_personal and t.amount > 0]
        personal_transactions  = [t for t in all_transactions if t.is_personal and t.amount > 0]
        refund_transactions    = [t for t in all_transactions if t.amount < 0]

        return AnalyticsSummary(
            total_business=round(sum(t.amount for t in business_transactions), 2),
            total_personal=round(sum(t.amount for t in personal_transactions), 2),
            total_refunds=round(sum(abs(t.amount) for t in refund_transactions), 2),
            tx_count=len(all_transactions),
            flagged_count=sum(1 for t in all_transactions if t.is_flagged),
        )

    def by_category(self) -> dict[str, float]:
        """
        Returns total business expenses grouped by category.

        Returns:
            Dict mapping category display name to total amount,
            sorted by total descending.
        """
        totals: dict[str, float] = defaultdict(float)

        for transaction in self._transaction_repo.get_all(exclude_personal=True):
            if transaction.amount > 0:
                totals[transaction.category.value] += transaction.amount

        return dict(
            sorted(
                {k: round(v, 2) for k, v in totals.items()}.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        )

    def by_month(self) -> dict[str, float]:
        """
        Returns total business expenses grouped by month.

        Returns:
            Dict with keys in "YYYY-MM" format (e.g. {"2025-01": 270.50}),
            sorted chronologically.
        """
        totals: dict[str, float] = defaultdict(float)

        for transaction in self._transaction_repo.get_all(exclude_personal=True):
            if transaction.amount > 0:
                month_key = transaction.date.strftime("%Y-%m")
                totals[month_key] += transaction.amount

        return {k: round(v, 2) for k, v in sorted(totals.items())}

    def by_source(self) -> dict[str, float]:
        """
        Returns total expenses grouped by payment source label.

        Returns:
            Dict mapping source label to total positive amount.
        """
        source_labels = {
            source.id: source.label
            for source in self._source_repo.get_all()
        }

        totals: dict[str, float] = defaultdict(float)

        for transaction in self._transaction_repo.get_all():
            if transaction.amount > 0:
                label = source_labels.get(transaction.source_id, f"Source {transaction.source_id}")
                totals[label] += transaction.amount

        return {k: round(v, 2) for k, v in totals.items()}