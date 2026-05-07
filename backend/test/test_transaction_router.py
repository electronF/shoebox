"""
HTTP-level tests for the /transactions router.

Uses the api_client fixture which runs against an in-memory DB
with no real parsers — only the API layer and service layer are exercised.
"""

import pytest
from datetime import date

from backend.core.enums import Category, SourceType
from backend.core.models import PaymentSource
from backend.infrastructure.db.repositories import SQLSourceRepository


@pytest.fixture
def existing_source(db_session) -> PaymentSource:
    """Creates and returns a payment source available for transaction creation."""
    return SQLSourceRepository(db_session).save(PaymentSource(
        id=None,
        label="Visa *4829",
        source_type=SourceType.CREDIT_CARD,
        last_four="4829",
        created_at=date.today(),
    ))


def test_create_manual_transaction(api_client, existing_source):
    """POST /transactions must return 201 and the created transaction."""
    payload = {
        "date":        "2025-01-22",
        "description": "Bureau en Gros — manual entry",
        "amount":      40.80,
        "category":    Category.SUPPLIES.value,
        "source_id":   existing_source.id,
    }

    response = api_client.post("/transactions/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "Bureau en Gros — manual entry"
    assert data["amount"]      == 40.80
    assert data["entry_method"] == "manual"
    assert data["id"].startswith("TXN-")


def test_get_transaction_not_found(api_client):
    """GET /transactions/{id} must return 404 for an unknown ID."""
    response = api_client.get("/transactions/TXN-999999-99999")
    assert response.status_code == 404


def test_create_transaction_rejects_zero_amount(api_client, existing_source):
    """POST /transactions with amount=0 must return 422 Unprocessable Entity."""
    payload = {
        "date":        "2025-01-22",
        "description": "Invalid transaction",
        "amount":      0.0,
        "source_id":   existing_source.id,
    }

    response = api_client.post("/transactions/", json=payload)
    assert response.status_code == 422


def test_list_transactions_returns_empty_initially(api_client):
    """GET /transactions on an empty DB must return an empty items list."""
    response = api_client.get("/transactions/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"]  == []
    assert data["total"]  == 0


def test_update_transaction_category(api_client, existing_source):
    """PATCH /transactions/{id} must update only the provided fields."""
    # Create first
    create_response = api_client.post("/transactions/", json={
        "date":        "2025-02-01",
        "description": "Unknown vendor",
        "amount":      25.00,
        "source_id":   existing_source.id,
    })
    transaction_id = create_response.json()["id"]

    # Patch category only
    patch_response = api_client.patch(
        f"/transactions/{transaction_id}",
        json={"category": Category.TRANSPORT.value},
    )

    assert patch_response.status_code == 200
    assert patch_response.json()["category"] == Category.TRANSPORT.value
    # Other fields must remain unchanged
    assert patch_response.json()["description"] == "Unknown vendor"


def test_delete_transaction(api_client, existing_source):
    """DELETE /transactions/{id} must return 204 and the transaction must be gone."""
    create_response = api_client.post("/transactions/", json={
        "date":        "2025-03-01",
        "description": "To be deleted",
        "amount":      10.00,
        "source_id":   existing_source.id,
    })
    transaction_id = create_response.json()["id"]

    delete_response = api_client.delete(f"/transactions/{transaction_id}")
    assert delete_response.status_code == 204

    get_response = api_client.get(f"/transactions/{transaction_id}")
    assert get_response.status_code == 404