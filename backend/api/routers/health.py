"""Health check endpoint."""

from fastapi import APIRouter
from backend.core.config import settings
from backend.schemas.common import HealthCheck

router = APIRouter()

@router.get("/health", response_model=HealthCheck, tags=["Health"])
def health_check() -> HealthCheck:
    """Returns API status and version. Used by load balancers and monitoring."""
    return HealthCheck(version=settings.app_version)