"""
Keyword-based transaction categorization rules.

Open/Closed Principle in practice:
    Adding support for a new merchant = adding one entry to RULES.
    The categorize() function never needs to change.

Each rule is a tuple of:
    (keywords, category, is_personal)

where keywords is a list of uppercase substrings to match against
the transaction description.
"""

import logging
from typing import Optional

from backend.core.enums import Category

logger = logging.getLogger(__name__)

# 
# Rule table — order matters: first match wins.
# Place more specific rules before more general ones.
# 
RULES: list[tuple[list[str], Category, bool]] = [
    # Software & subscriptions
    (["GOOGLE *WORKSPACE", "GOOGLE WORKSPACE"],  Category.SOFTWARE,   False),
    (["ADOBE"],                                   Category.SOFTWARE,   False),
    (["CANVA"],                                   Category.SOFTWARE,   False),
    (["NAMECHEAP"],                               Category.SOFTWARE,   False),

    # E-commerce platform
    (["SHOPIFY"],                                 Category.ECOMMERCE,  False),

    # Coworking
    (["VRBO COWORKING", "COWORKING"],             Category.COWORKING,  False),

    # Supplies & shipping
    (["AMAZON.CA *OFFICE", "AMAZON"],             Category.SUPPLIES,   False),
    (["STAPLES", "BUREAU EN GROS"],               Category.SUPPLIES,   False),
    (["POSTES CANADA", "CANADA POST"],            Category.SUPPLIES,   False),
    (["JEAN COUTU"],                              Category.SUPPLIES,   False),
    (["CHEN'S ART", "CHEN"],                      Category.SUPPLIES,   False),

    # Transport
    (["WAYMO", "STATIONNEMENT", "PARKING"],       Category.TRANSPORT,  False),

    # Meals & client entertainment
    (["CAFE", "MYRIADE", "PETIT DEP", "REST."],  Category.MEALS,      False),

    # Personal — explicitly excluded from business deductions
    (["NETFLIX"],                                 Category.PERSONAL,   True),
    (["PETCO"],                                   Category.PERSONAL,   True),
]

# Merchants known to produce duplicate charges — flagged automatically
_DUPLICATE_PRONE_MERCHANTS: list[str] = ["ADOBE", "SHOPIFY", "VRBO"]


def categorize(
    description: str,
    amount: float,  # noqa: ARG001 — reserved for future amount-based rules
) -> tuple[Category, bool, bool, Optional[str]]:
    """
    Classifies a transaction description into a Category.

    Iterates through RULES in order and returns on the first keyword match.
    Falls back to UNCATEGORIZED if no rule matches.

    Args:
        description: Transaction description string (any case).
        amount:      Transaction amount in CAD. Reserved for future
                     amount-based anomaly rules (e.g. unusually large amounts).

    Returns:
        A 4-tuple of:
            - category (Category enum)
            - is_personal (bool) — True if this is a personal expense
            - is_flagged (bool)  — True if this should be reviewed
            - flag_reason (str | None) — Human-readable reason if flagged

    Example::

        category, is_personal, is_flagged, reason = categorize("NETFLIX.COM", 16.99)
        # → (Category.PERSONAL, True, True, "Personal expense on business card")
    """
    description_upper = description.upper()

    for keywords, category, is_personal in RULES:
        if any(keyword in description_upper for keyword in keywords):
            is_flagged  = is_personal
            flag_reason = "Personal expense on business card" if is_personal else None

            logger.debug(
                "categorize: '%s' → %s (personal=%s)",
                description, category.value, is_personal,
            )
            return category, is_personal, is_flagged, flag_reason

    logger.debug("categorize: '%s' → UNCATEGORIZED (no rule matched)", description)
    return Category.UNCATEGORIZED, False, False, None


def is_duplicate_prone(description: str) -> bool:
    """
    Returns True if the merchant is known to sometimes generate duplicate charges.

    Used by the anomaly detection layer to flag transactions for review.

    Args:
        description: Transaction description string.

    Returns:
        True if the merchant appears in the duplicate-prone list.
    """
    description_upper = description.upper()
    return any(merchant in description_upper for merchant in _DUPLICATE_PRONE_MERCHANTS)