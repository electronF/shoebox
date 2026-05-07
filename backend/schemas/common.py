"""
Pydantic schemas shared across all routers.

These generic models are used for paginated responses,
standardized errors, and health checks.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response.

    Attributes:
        items: List of elements for the current page.
        total: Total number of elements (across all pages).
        page:  Page number (starts at 1).
        size:  Number of elements per page.
    """

    items: list[T]
    total: int
    page:  int = Field(ge=1)
    size:  int = Field(ge=1, le=200)


class ErrorDetail(BaseModel):
    """
    Detail of an error returned by the API.

    Attributes:
        code:    Machine-readable error code (e.g., "NOT_FOUND", "VALIDATION_ERROR").
        message: Human-readable message.
        field:   Target field, if the error is related to field validation.
    """

    code:    str
    message: str
    field:   str | None = None


class HealthCheck(BaseModel):
    """Response from the GET /health endpoint."""

    status:   str = "ok"
    version:  str
    database: str = "connected"