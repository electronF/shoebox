"""
HTTP client for the Shoebox FastAPI backend.

All views call this module — never requests directly.
If the backend URL changes, only this file needs updating.
"""

import logging
from typing import Any, Optional

import requests

log = logging.getLogger(__name__)

_BASE_URL = "http://localhost:8000"
_TIMEOUT  = 10  # seconds


def _sanitize_params(params: Optional[dict]) -> Optional[dict]:
    """Drops None values and lowercases Python booleans for FastAPI.

    Args:
        params: Raw query parameter dict, possibly containing None values
                or Python bool literals.

    Returns:
        Cleaned dict, or None if there is nothing to send.
    """
    if not params:
        return None
    return {
        k: str(v).lower() if isinstance(v, bool) else v
        for k, v in params.items()
        if v is not None
    }


def _get(path: str, params: Optional[dict] = None) -> Any:
    """
    Performs a GET request to the backend.

    Args:
        path:   API path (e.g. "/transactions").
        params: Optional query parameters.

    Returns:
        Parsed JSON response, or empty dict on error.
    """
    try:
        response = requests.get(
            f"{_BASE_URL}{path}",
            params=_sanitize_params(params),
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        log.error("GET %s failed: %s", path, exc)
        return {}


def _post(path: str, json: Optional[dict] = None) -> Any:
    """
    Performs a POST request to the backend.

    Args:
        path: API path.
        json: Request body as dict.

    Returns:
        Parsed JSON response, or empty dict on error.
    """
    try:
        response = requests.post(
            f"{_BASE_URL}{path}",
            json=json,
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        log.error("POST %s failed: %s", path, exc)
        return {}


def _patch(path: str, json: Optional[dict] = None) -> Any:
    """Performs a PATCH request to the backend."""
    try:
        response = requests.patch(
            f"{_BASE_URL}{path}",
            json=json,
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        log.error("PATCH %s failed: %s", path, exc)
        return {}


def _delete(path: str) -> bool:
    """
    Performs a DELETE request to the backend.

    Returns:
        True if the resource was deleted (HTTP 204), False otherwise.
    """
    try:
        response = requests.delete(f"{_BASE_URL}{path}", timeout=_TIMEOUT)
        return response.status_code == 204
    except requests.RequestException as exc:
        log.error("DELETE %s failed: %s", path, exc)
        return False



# Domain-specific API calls
def get_analytics_summary() -> dict:
    """Returns top-level financial KPIs."""
    return _get("/analytics/summary")


def get_by_category() -> dict:
    """Returns expenses grouped by category."""
    return _get("/analytics/by-category")


def get_by_month() -> dict:
    """Returns expenses grouped by month."""
    return _get("/analytics/by-month")


def get_by_source() -> dict:
    """Returns expenses grouped by payment source."""
    return _get("/analytics/by-source")


def get_transactions(
    source_id: Optional[str]  = None,
    category:  Optional[str]  = None,
    exclude_personal: bool     = False,
    page: int                  = 1,
    size: int                  = 50,
) -> dict:
    """Returns paginated transactions with optional filters."""
    return _get("/transactions", params={
        "source_id":        source_id,
        "category":         category,
        "exclude_personal": exclude_personal,
        "page":             page,
        "size":             size,
    })


def create_transaction(payload: dict) -> dict:
    """Creates a manual transaction."""
    return _post("/transactions", json=payload)


def update_transaction(transaction_id: str, payload: dict) -> dict:
    """Partially updates a transaction."""
    return _patch(f"/transactions/{transaction_id}", json=payload)


def delete_transaction(transaction_id: str) -> bool:
    """Deletes a transaction by ID."""
    return _delete(f"/transactions/{transaction_id}")


def get_sources() -> list:
    """Returns all payment sources."""
    result = _get("/sources")
    return result if isinstance(result, list) else []


def create_source(payload: dict) -> dict:
    """Registers a new payment source."""
    return _post("/sources", json=payload)


def get_files() -> list:
    """Returns all ingested files with statistics."""
    result = _get("/files")
    return result if isinstance(result, list) else []


def upload_files(
    files: list[tuple[str, bytes, str]],
    doc_type:     str,
    source_label: str,
    source_type:  str,
) -> list[dict]:
    """
    Uploads one or more files to the ingestion endpoint.

    Args:
        files:        List of (filename, content_bytes, mime_type) tuples.
        doc_type:     Document type enum value (e.g. "REC").
        source_label: Payment source label.
        source_type:  Payment source type enum value.

    Returns:
        List of IngestionResult dicts, one per file.
    """
    try:
        multipart_files = [
            ("files", (filename, content, mime))
            for filename, content, mime in files
        ]
        response = requests.post(
            f"{_BASE_URL}/files/upload",
            files=multipart_files,
            data={
                "doc_type":     doc_type,
                "source_label": source_label,
                "source_type":  source_type,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        log.error("POST /files/upload failed: %s", exc)
        return []


def get_invoices(status: Optional[str] = None) -> list:
    """Returns all invoices, optionally filtered by status."""
    result = _get("/invoices", params={"payment_status": status})
    return result if isinstance(result, list) else []


def update_invoice(invoice_id: str, payload: dict) -> dict:
    """Partially updates an invoice (status, date_paid, etc.)."""
    return _patch(f"/invoices/{invoice_id}", json=payload)


def create_invoice(payload: dict) -> dict:
    """Creates a new issued invoice record."""
    return _post("/invoices", json=payload)


def get_actions(status: Optional[str] = None) -> list:
    """Returns action items, optionally filtered by status."""
    result = _get("/actions", params={"status": status})
    return result if isinstance(result, list) else []

def parse_file_preview(
    filename:  str,
    content:   bytes,
    doc_type:  str,
) -> dict:
    """
    Sends a file for parsing without saving to the database.

    Args:
        filename: Original filename.
        content:  Raw file bytes.
        doc_type: Document type ID.

    Returns:
        Dict with "status" and "data" keys.
        data contains extracted field values.
    """
    try:
        response = requests.post(
            f"{_BASE_URL}/files/parse",
            files={"file": (filename, content, _mime_for(filename))},
            data={"doc_type": doc_type},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        log.error("POST /files/parse failed: %s", exc)
        return {"status": "error", "data": {}}


def get_recurring() -> dict:
    """
    Returns detected recurring patterns and a 3-month forecast.

    Returns:
        Dict with "patterns" (list of pattern dicts) and
        "forecast" (list of forecast entry dicts).
    """
    result = _get("/analytics/recurring")
    if isinstance(result, dict):
        return result
    return {"patterns": [], "forecast": []}


def _mime_for(filename: str) -> str:
    """Returns MIME type for a filename."""
    ext = filename.rsplit(".", 1)[-1].lower()
    return {
        "pdf":  "application/pdf",
        "png":  "image/png",
        "jpg":  "image/jpeg",
        "jpeg": "image/jpeg",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }.get(ext, "application/octet-stream")