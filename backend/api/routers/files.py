"""
FastAPI Router for file uploads and management.

The POST /files/upload endpoint is the primary entry point
for the ingestion flow: it receives files, validates their types,
and delegates to the IngestionService.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from backend.api.dependencies import get_file_repo, get_ingestion_service
from backend.core.enums import DocType, SourceType
from backend.infrastructure.db.repositories import SQLFileRepository
from backend.schemas.file import IngestionResult, UploadedFileRead
from backend.services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)
router = APIRouter()

# Accepted formats per document type — enforced at the API level
_ACCEPTED_FORMATS: dict[DocType, set[str]] = {
    DocType.RECEIPT:   {".jpg", ".jpeg", ".png", ".pdf"},
    DocType.STATEMENT: {".pdf", ".xlsx"},
    DocType.INVOICE:   {".pdf", ".xlsx"},
    DocType.NOTES:     {".txt"},
}


def _validate_file_format(filename: str, doc_type: DocType) -> None:
    """
    Validates that the file extension matches the document type.

    Args:
        filename: Name of the uploaded file.
        doc_type: Document type declared by the user.

    Raises:
        HTTPException 422: If the format is not accepted for this type.
    """
    from pathlib import Path

    extension = Path(filename).suffix.lower()
    accepted  = _ACCEPTED_FORMATS.get(doc_type, set())

    if extension not in accepted:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Format '{extension}' not accepted for type '{doc_type.value}'. "
                f"Expected formats: {sorted(accepted)}"
            ),
        )



@router.post(
    "/upload",
    response_model=list[IngestionResult],
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest one or more files",
    description=(
        "Receives files, validates their format based on document type, "
        "triggers parsing, and persists extracted transactions."
    ),
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "files": {
                                "type": "array",
                                "items": {"type": "string", "format": "binary"},
                                "description": "Files to ingest.",
                            },
                            "doc_type": {
                                "type": "string",
                                "enum": ["REC", "STMT", "INV", "NOTE"],
                                "description": "Declared document type.",
                            },
                            "source_label": {
                                "type": "string",
                                "description": "Payment source label (e.g. 'Visa *4829').",
                            },
                            "source_type": {
                                "type": "string",
                                "enum": ["credit_card", "cash", "personal"],
                                "description": "Type of payment source.",
                            },
                        },
                        "required": ["files", "doc_type", "source_label", "source_type"],
                    }
                }
            }
        }
    },
)
async def upload_files(
    files:        Annotated[list[UploadFile], File(description="Files to ingest.")],
    doc_type:      Annotated[DocType,          Form(description="Declared document type.")],
    source_label: Annotated[str,              Form(description="Payment source label.")],
    source_type:  Annotated[SourceType,       Form(description="Source type (credit_card, cash, personal).")],
    service: IngestionService = Depends(get_ingestion_service),
) -> list[IngestionResult]:
    """
    Main multi-file ingestion endpoint.

    Each file is processed independently: a failure on one 
    does not interrupt the processing of others.

    Args:
        files:        List of uploaded files (multipart/form-data).
        doc_type:      Document type declared by the user.
        source_label: Source label (e.g., "Visa *4829").
        source_type:  Payment source type.
        service:      Injected ingestion service.

    Returns:
        List of ingestion results, one per file.
    """
    results: list[IngestionResult] = []

    for uploaded_file in files:
        filename = uploaded_file.filename or "unnamed_file"

        # Validate format before reading content
        try:
            _validate_file_format(filename, doc_type)
        except HTTPException as format_error:
            results.append(IngestionResult(
                file_id=None,
                filename=filename,
                status="wrong_format",
                errors=[format_error.detail],
            ))
            continue

        content = await uploaded_file.read()

        result = service.ingest(
            filename=filename,
            content=content,
            doc_type=doc_type,
            source_label=source_label,
            source_type=source_type,
        )
        results.append(result)
        logger.info(
            "File '%s' ingested: %s (%d transactions)",
            filename, result.status, result.tx_count,
        )

    return results


@router.get(
    "/",
    response_model=list[UploadedFileRead],
    summary="List ingested files",
)
def list_files(
    repo: SQLFileRepository = Depends(get_file_repo),
) -> list[UploadedFileRead]:
    """
    Returns the list of all ingested files with their statistics.

    Args:
        repo: Injected repository.

    Returns:
        List of files sorted by upload date (descending).
    """
    return [UploadedFileRead.model_validate(f, from_attributes=True) for f in repo.get_all()]


@router.post(
    "/parse",
    summary="Parse a file without saving to database",
    description=(
        "Extracts data from a file using OCR or parsing "
        "and returns the result. Nothing is saved to the database. "
        "Use POST /files/upload to persist after user validation."
    ),
)
async def parse_file_preview(
    file:        UploadFile          = File(...),
    doc_type:    DocType             = Form(...),
    service:     IngestionService    = Depends(get_ingestion_service),
) -> dict:
    """
    Parses a single file and returns extracted field values.

    Args:
        file:     File to parse.
        doc_type: Declared document type.
        service:  Injected ingestion service.

    Returns:
        Dict of extracted fields — no DB writes performed.
    """
    from pathlib import Path
    import tempfile, os

    filename  = file.filename or "upload"
    content   = await file.read()
    extension = Path(filename).suffix.lower()

    # Validate format
    try:
        _validate_file_format(filename, doc_type)
    except HTTPException:
        return {"status": "wrong_format", "data": {}}

    # Write to temp file for parser
    with tempfile.NamedTemporaryFile(
        suffix=extension, delete=False
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        parser = next(
            (p for p in service._parsers if p.can_parse(filename)),
            None,
        )
        if not parser:
            return {"status": "no_parser", "data": {}}

        transactions = parser.parse(tmp_path, "preview", "preview")

        # Statement: return header metadata + all transaction rows
        if doc_type == DocType.STATEMENT:
            metadata: dict = {}
            if hasattr(parser, "extract_metadata"):
                metadata = parser.extract_metadata(tmp_path)

            tx_rows = [
                {
                    "date":        str(tx.date),
                    "description": tx.description,
                    "amount":      str(tx.amount),
                    "ref":         tx.ref or "",
                }
                for tx in transactions
            ]
            return {
                "status": "ok" if transactions else "empty",
                "data":   {**metadata, "transactions": tx_rows},
            }

        # Invoice (xlsx multi-row): return all rows for editable table
        if doc_type == DocType.INVOICE:
            if hasattr(parser, "extract_rows"):
                inv_rows = parser.extract_rows(tmp_path)
                return {
                    "status": "ok" if inv_rows else "empty",
                    "data":   {"rows": inv_rows},
                }

        # Notes: return raw text content for pre-population in the textarea
        if doc_type == DocType.NOTES:
            raw_text = Path(tmp_path).read_text(encoding="utf-8", errors="replace")
            return {"status": "ok", "data": {"note_text": raw_text}}

        # Receipt / other: return first transaction fields
        if transactions:
            tx = transactions[0]
            return {
                "status": "ok",
                "data": {
                    "merchant":       tx.description,
                    "date":           str(tx.date),
                    "amount":         str(abs(tx.amount)),
                    "total":          str(abs(tx.amount)),
                    "category":       tx.category.value,
                    "ref":            tx.ref or "",
                    "ocr_confidence": tx.ocr_confidence,
                },
            }

        return {"status": "empty", "data": {}}

    finally:
        os.unlink(tmp_path)
