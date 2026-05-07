"""
FastAPI Router for dashboard analytics and KPIs.

These endpoints are read-only and never modify the
state of the database.
"""

from dataclasses import asdict
from datetime import date

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_analytics_service, get_recurring_service
from backend.services.analytics_service import AnalyticsService, AnalyticsSummary
from backend.services.recurring_service import RecurringService

router = APIRouter()


@router.get(
    "/summary",
    response_model=AnalyticsSummary,
    summary="Global financial summary",
    description="Returns main KPIs: total business, personal, refunds, and income.",
)
def get_summary(
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsSummary:
    """Calculates and returns the financial summary for all periods."""
    return service.compute_summary()


@router.get(
    "/by-category",
    response_model=dict[str, float],
    summary="Expenses by category",
)
def get_by_category(
    service: AnalyticsService = Depends(get_analytics_service),
) -> dict[str, float]:
    """Returns total business expenses grouped by category."""
    return service.by_category()


@router.get(
    "/by-month",
    response_model=dict[str, float],
    summary="Expenses by month",
)
def get_by_month(
    service: AnalyticsService = Depends(get_analytics_service),
) -> dict[str, float]:
    """
    Returns monthly total for business expenses.

    Returns:
        Dict with keys in "YYYY-MM" format (e.g., {"2026-01": 270.50}).
    """
    return service.by_month()


@router.get(
    "/by-source",
    response_model=dict[str, float],
    summary="Expenses by payment source",
)
def get_by_source(
    service: AnalyticsService = Depends(get_analytics_service),
) -> dict[str, float]:
    """Returns total expenses grouped by payment source."""
    return service.by_source()


@router.get(
    "/recurring",
    summary="Recurring expense patterns and 3-month forecast",
)
def get_recurring(
    service: RecurringService = Depends(get_recurring_service),
) -> dict:
    """
    Detects recurring expense patterns and projects them forward.

    Returns:
        Dict with "patterns" (list of detected RecurringPattern dicts)
        and "forecast" (list of ForecastEntry dicts for next 3 months).
    """
    patterns = service.detect_patterns()
    now      = date.today()
    forecast = service.forecast(patterns, last_month=now.month, year=now.year)
    return {
        "patterns": [asdict(p) for p in patterns],
        "forecast": [asdict(f) for f in forecast],
    }