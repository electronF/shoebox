"""
Meaningful identifier generator for all entities.

Format: PREFIX-YYMMDD-NNNNN
Example: REC-250122-00001

This format allows for an immediate understanding of the type and date
of an entity just by reading its ID, without requiring a database query.

The sequencer is implemented in Python (rather than SQL) to remain
compatible with SQLite, PostgreSQL, and MySQL without modification.
"""

import logging
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.core.enums import DocType

logger = logging.getLogger(__name__)

# Table mapping → default prefix
_TABLE_PREFIXES: dict[str, str] = {
    "transactions":       "TXN",
    "uploaded_files":     "FILE",
    "payment_sources":    "SRC",
    "recurring_patterns": "PAT",
    "forecasts":          "FCST",
    "anomalies":          "ANO",
    "action_items":       "ACT",
    "invoices":           "INV",
}

# Document types override the default prefix for uploaded_files
_DOC_TYPE_PREFIXES: dict[DocType, str] = {
    DocType.RECEIPT:   "REC",
    DocType.STATEMENT: "STMT",
    DocType.INVOICE:   "INV",
    DocType.NOTES:     "NOTE",
}


def generate_id(
    session: Session,
    table_name: str,
    doc_type: DocType | None = None,
) -> str:
    """
    Generates a unique meaningful ID for an entity.

    Reads the existing MAX(id) for the given prefix and today's date,
    then increments the sequencer by 1. Thread-safe thanks to the
    encapsulating SQLAlchemy transaction.

    Args:
        session:    Active SQLAlchemy session.
        table_name: Target table name (key in _TABLE_PREFIXES).
        doc_type:   Document type to override the prefix 
                    (used for uploaded_files and transactions 
                    originating from a typed file).

    Returns:
        ID in the format "PREFIX-YYMMDD-NNNNN" (e.g.: "REC-250506-00001").

    Raises:
        ValueError: If table_name is unknown and doc_type is None.

    Example::

        tx_id = generate_id(session, "transactions", DocType.RECEIPT)
        # → "REC-260506-00001"
    """
    # Determine the prefix
    if doc_type is not None:
        prefix = _DOC_TYPE_PREFIXES.get(doc_type, "TXN")
    elif table_name in _TABLE_PREFIXES:
        prefix = _TABLE_PREFIXES[table_name]
    else:
        raise ValueError(
            f"Unknown table '{table_name}' and no doc_type provided. "
            f"Supported tables: {list(_TABLE_PREFIXES.keys())}"
        )

    today_str = date.today().strftime("%y%m%d")
    pattern   = f"{prefix}-{today_str}-%"

    # Read the last sequencer of the day for this prefix
    last_id: str | None = session.execute(
        text(f"SELECT MAX(id) FROM {table_name} WHERE id LIKE :pattern"),
        {"pattern": pattern},
    ).scalar()

    if last_id:
        # Extract and increment the counter (last 5 characters)
        last_sequence = int(last_id.split("-")[-1])
        next_sequence = last_sequence + 1
    else:
        next_sequence = 1

    new_id = f"{prefix}-{today_str}-{next_sequence:05d}"
    logger.debug("Generated ID for '%s': %s", table_name, new_id)
    return new_id