"""CRUD router for action items (todos extracted from notes or created manually)."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from backend.api.dependencies import get_session
from backend.infrastructure.db.repositories import SQLActionRepository
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/")
def list_actions(
    status: Optional[str] = Query(default=None, description="Filter by 'open' or 'done'."),
    db: Session = Depends(get_session),
):
    """Returns all action items, optionally filtered by status."""
    return SQLActionRepository(db).get_all(status=status)

@router.patch("/{action_id}/status")
def update_action_status(action_id: str, new_status: str, db: Session = Depends(get_session)):
    """Updates the status of an action item ('open' or 'done')."""
    SQLActionRepository(db).update_status(action_id, new_status)
    return {"id": action_id, "status": new_status}