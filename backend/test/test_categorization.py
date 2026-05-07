"""Tests for the keyword-based categorization rules."""

import pytest

from backend.core.enums import Category
from backend.infrastructure.categorization.rules import categorize, is_duplicate_prone


@pytest.mark.parametrize("description, expected_category, expected_personal", [
    ("GOOGLE *WORKSPACE",          Category.SOFTWARE,    False),
    ("ADOBE *CREATIVE CL",         Category.SOFTWARE,    False),
    ("CANVA.COM",                  Category.SOFTWARE,    False),
    ("SHOPIFY* 1234567",           Category.ECOMMERCE,   False),
    ("VRBO COWORKING MTL",         Category.COWORKING,   False),
    ("AMAZON.CA *OFFICE",          Category.SUPPLIES,    False),
    ("STAPLES #0312",              Category.SUPPLIES,    False),
    ("POSTES CANADA",              Category.SUPPLIES,    False),
    ("WAYMO BUSINESS *X MONTREAL", Category.TRANSPORT,   False),
    ("SQ *CAFE MYRIADE",           Category.MEALS,       False),
    ("NETFLIX.COM",                Category.PERSONAL,    True),
    ("PETCO #4521",                Category.PERSONAL,    True),
    ("UNKNOWN VENDOR XYZ",         Category.UNCATEGORIZED, False),
])
def test_categorize_known_merchants(description, expected_category, expected_personal):
    """
    categorize() must return the correct category and personal flag
    for all merchants defined in the RULES table.
    """
    category, is_personal, _, _ = categorize(description, 10.0)

    assert category == expected_category, (
        f"'{description}': expected {expected_category}, got {category}"
    )
    assert is_personal == expected_personal, (
        f"'{description}': expected is_personal={expected_personal}, got {is_personal}"
    )


def test_personal_transaction_is_flagged():
    """Personal transactions must always set is_flagged=True."""
    _, _, is_flagged, flag_reason = categorize("NETFLIX.COM", 16.99)

    assert is_flagged is True
    assert flag_reason is not None
    assert len(flag_reason) > 0


def test_business_transaction_is_not_flagged():
    """Non-personal transactions must not be flagged."""
    _, _, is_flagged, flag_reason = categorize("GOOGLE *WORKSPACE", 8.28)

    assert is_flagged is False
    assert flag_reason is None


def test_categorize_is_case_insensitive():
    """categorize() must match regardless of input case."""
    category_upper, _, _, _ = categorize("NETFLIX.COM", 16.99)
    category_lower, _, _, _ = categorize("netflix.com", 16.99)

    assert category_upper == category_lower


@pytest.mark.parametrize("description, expected", [
    ("ADOBE *CREATIVE CL", True),
    ("SHOPIFY* 1234567",   True),
    ("VRBO COWORKING MTL", True),
    ("POSTES CANADA",      False),
    ("AMAZON.CA *OFFICE",  False),
])
def test_is_duplicate_prone(description, expected):
    """is_duplicate_prone() must identify merchants known to generate duplicates."""
    assert is_duplicate_prone(description) == expected