"""Tests for the ID generation utility."""

import pytest
from unittest.mock import MagicMock

from backend.core.enums import DocType
from backend.infrastructure.db.id_generator import generate_id


def test_generate_id_returns_correct_format(db_session):
    """Generated ID must match the PREFIX-YYMMDD-NNNNN pattern."""
    import re

    generated = generate_id(db_session, "transactions")
    assert re.match(r"^[A-Z]+-\d{6}-\d{5}$", generated), (
        f"ID '{generated}' does not match expected format PREFIX-YYMMDD-NNNNN"
    )


def test_generate_id_uses_doc_type_prefix(db_session):
    """When doc_type is provided, its prefix overrides the table default."""
    generated = generate_id(db_session, "uploaded_files", doc_type=DocType.RECEIPT)
    assert generated.startswith("REC-"), (
        f"Expected prefix 'REC-' for DocType.RECEIPT, got '{generated}'"
    )


def test_generate_id_increments_sequence(db_session):
    """Two calls on the same day must produce different sequential IDs."""
    first  = generate_id(db_session, "action_items")
    # Simulate a persisted row so the second call finds it
    db_session.execute(
        __import__("sqlalchemy").text(
            "INSERT INTO action_items (id, text, status, created_at) "
            "VALUES (:id, 'test', 'open', date('now'))"
        ),
        {"id": first},
    )
    second = generate_id(db_session, "action_items")

    first_seq  = int(first.split("-")[-1])
    second_seq = int(second.split("-")[-1])

    assert second_seq == first_seq + 1, (
        f"Expected sequence {first_seq + 1}, got {second_seq}"
    )


def test_generate_id_raises_for_unknown_table(db_session):
    """Unknown table names without doc_type must raise ValueError."""
    with pytest.raises(ValueError, match="unknown_table"):
        generate_id(db_session, "unknown_table")