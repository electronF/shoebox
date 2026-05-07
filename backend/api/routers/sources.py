# backend/api/routers/sources.py

"""
CRUD router for payment sources.

Payment sources are also created automatically during file ingestion
when an unknown source label is encountered. This router allows
manual registration and listing.
"""

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.dependencies import get_session
from backend.core.enums import SourceType
from backend.core.models import PaymentSource
from backend.infrastructure.db.repositories import SQLSourceRepository
from backend.schemas.source import PaymentSourceCreate, PaymentSourceRead

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/",
    response_model=list[PaymentSourceRead],
    summary="List all payment sources",
)
def list_sources(
    db: Session = Depends(get_session),
) -> list[PaymentSourceRead]:
    """
    Returns all registered payment sources.

    Sources are created automatically during file ingestion,
    or manually via POST /sources.
    """
    repo    = SQLSourceRepository(db)
    sources = repo.get_all()
    return [
        PaymentSourceRead.model_validate(s, from_attributes=True)
        for s in sources
    ]


@router.post(
    "/",
    response_model=PaymentSourceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new payment source",
)
def create_source(
    payload: PaymentSourceCreate,
    db: Session = Depends(get_session),
) -> PaymentSourceRead:
    """
    Manually registers a new payment source.

    If a source with the same label already exists, returns 409.

    Args:
        payload: Source label, type, and optional last four digits.
        db:      Injected database session.

    Returns:
        The created payment source with its generated ID.
    """
    repo = SQLSourceRepository(db)

    # Prevent duplicates
    existing = repo.find_by_label(payload.label)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A source with label '{payload.label}' already exists (id: {existing.id}).",
        )

    source = PaymentSource(
        id=None,
        label=payload.label,
        source_type=payload.source_type,
        last_four=payload.last_four,
        created_at=date.today(),
    )

    saved = repo.save(source)
    logger.info("Payment source created: %s — '%s'", saved.id, saved.label)

    return PaymentSourceRead.model_validate(saved, from_attributes=True)


@router.get(
    "/{source_id}",
    response_model=PaymentSourceRead,
    summary="Get a payment source by ID",
)
def get_source(
    source_id: str,
    db: Session = Depends(get_session),
) -> PaymentSourceRead:
    """
    Returns a single payment source by its ID.

    Args:
        source_id: ID in the format SRC-YYMMDD-NNNNN.
        db:        Injected database session.

    Raises:
        HTTPException 404: If the source does not exist.
    """
    repo   = SQLSourceRepository(db)
    source = repo.find_by_id(source_id)

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source '{source_id}' not found.",
        )

    return PaymentSourceRead.model_validate(source, from_attributes=True)