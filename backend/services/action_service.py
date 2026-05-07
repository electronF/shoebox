"""
CRUD service for action items (todos and completed tasks).

Action items originate either from notes.txt parsing or from
manual creation via the API.
"""

import logging
from datetime import date
from typing import Optional

from backend.core.interfaces import IActionRepository
from backend.core.models import ActionItem

logger = logging.getLogger(__name__)

_VALID_STATUSES = {"open", "done"}


class ActionService:
    """
    Manages action item lifecycle: creation, retrieval, and status updates.

    Args:
        action_repo: Repository for action item persistence.
    """

    def __init__(self, action_repo: IActionRepository) -> None:
        self._action_repo = action_repo

    def list_actions(self, status: Optional[str] = None) -> list[ActionItem]:
        """
        Returns all action items, optionally filtered by status.

        Args:
            status: "open" or "done". Returns all statuses if None.

        Returns:
            List of ActionItem domain objects ordered by creation date.
        """
        return self._action_repo.get_all(status=status)

    def create(self, text: str, source_file: Optional[str] = None) -> ActionItem:
        """
        Creates a new open action item manually.

        Args:
            text:        The task description.
            source_file: Optional filename this action was derived from.

        Returns:
            The persisted ActionItem with a generated ID.
        """
        action = ActionItem(
            id=None,
            text=text.strip(),
            status="open",
            source_file=source_file,
            created_at=date.today(),
        )
        saved = self._action_repo.save(action)
        logger.info("Action item created: %s — '%s'", saved.id, saved.text[:60])
        return saved

    def mark_done(self, action_id: str) -> bool:
        """
        Marks an action item as done.

        Args:
            action_id: ID of the action item to mark as completed.

        Returns:
            True if found and updated, False if not found.
        """
        return self._action_repo.update_status(action_id, "done")

    def reopen(self, action_id: str) -> bool:
        """
        Re-opens a previously completed action item.

        Args:
            action_id: ID of the action item to reopen.

        Returns:
            True if found and updated, False if not found.
        """
        return self._action_repo.update_status(action_id, "open")