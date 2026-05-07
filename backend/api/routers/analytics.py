"""
FastAPI Router for dashboard analytics and KPIs.

These endpoints are read-only and never modify the 
state of the database.
"""

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_analytics_service
from backend.services.analytics_service import AnalyticsService, AnalyticsSummary

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