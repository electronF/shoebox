"""
FastAPI Router for transactions.

The routers are intentionally thin (thin controllers):
they validate inputs via Pydantic, delegate to the service,
and return the serialized response. No business logic here.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.api.dependencies import get_transaction_service
from backend.core.enums import Category
from backend.schemas.common import PaginatedResponse
from backend.schemas.transaction import (
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)
from backend.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/",
    response_model=PaginatedResponse[TransactionRead],
    summary="List transactions",
    description="Returns all transactions with filtering and pagination.",
)
def list_transactions(
    source_id:        Optional[str]      = Query(default=None, description="Filter by payment source."),
    category:         Optional[Category] = Query(default=None, description="Filter by category."),
    exclude_personal: bool               = Query(default=False, description="Exclude personal expenses."),
    page:             int                = Query(default=1, ge=1),
    size:             int                = Query(default=50, ge=1, le=200),
    service: TransactionService = Depends(get_transaction_service),
) -> PaginatedResponse[TransactionRead]:
    """
    Returns paginated transactions based on filters.

    Args:
        source_id:        ID of the payment source (optional).
        category:         Expense category (optional).
        exclude_personal: If True, excludes personal expenses.
        page:             Page number (default: 1).
        size:             Page size (default: 50, max: 200).
        service:          Service injected by FastAPI.

    Returns:
        Paginated response containing the list of transactions.
    """
    transactions, total = service.list_transactions(
        source_id=source_id,
        category=category,
        exclude_personal=exclude_personal,
        page=page,
        size=size,
    )
    return PaginatedResponse(
        items=transactions,
        total=total,
        page=page,
        size=size,
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionRead,
    summary="Get a transaction",
)
def get_transaction(
    transaction_id: str,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionRead:
    """
    Returns a transaction by its ID.

    Args:
        transaction_id: Transaction ID (e.g., "REC-250122-00001").
        service:        Injected service.

    Returns:
        The found transaction.

    Raises:
        HTTPException 404: If the transaction does not exist.
    """
    transaction = service.get_by_id(transaction_id)
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found.",
        )
    return transaction


@router.post(
    "/",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a manual transaction",
)
def create_transaction(
    payload: TransactionCreate,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionRead:
    """
    Creates a transaction via manual entry (without a source file).

    Args:
        payload: Transaction data validated by Pydantic.
        service: Injected service.

    Returns:
        The created transaction with its generated ID.
    """
    created = service.create_manual(payload)
    logger.info("Manual transaction created: %s", created.id)
    return created


@router.patch(
    "/{transaction_id}",
    response_model=TransactionRead,
    summary="Update a transaction",
)
def update_transaction(
    transaction_id: str,
    payload: TransactionUpdate,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionRead:
    """
    Partially updates a transaction (semantic PATCH).

    Only the fields provided in the payload are modified.

    Args:
        transaction_id: ID of the transaction to update.
        payload:        Fields to modify (all optional).
        service:        Injected service.

    Returns:
        The updated transaction.

    Raises:
        HTTPException 404: If the transaction does not exist.
    """
    updated = service.update(transaction_id, payload)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found.",
        )
    return updated


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a transaction",
)
def delete_transaction(
    transaction_id: str,
    service: TransactionService = Depends(get_transaction_service),
) -> None:
    """
    Deletes a transaction.

    Args:
        transaction_id: ID of the transaction to delete.
        service:        Injected service.

    Raises:
        HTTPException 404: If the transaction does not exist.
    """
    deleted = service.delete(transaction_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found.",
        )