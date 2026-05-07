"""CRUD router for payment sources."""

from fastapi import APIRouter, Depends
from backend.api.dependencies import get_source_repo
from backend.infrastructure.db.repositories import SQLSourceRepository

router = APIRouter()

@router.get("/")
def list_sources(repo: SQLSourceRepository = Depends(get_source_repo)):
    """Returns all registered payment sources."""
    return repo.get_all()