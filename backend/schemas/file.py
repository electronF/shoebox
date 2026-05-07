"""Pydantic schemas for uploaded files and ingestion results."""

from datetime import date
from typing import Optional

from pydantic import BaseModel

from backend.core.enums import DocType, FileType


class UploadedFileRead(BaseModel):
    """Metadata of an ingested file returned by the API."""

    id:            str
    filename:      str
    file_type:     FileType
    doc_type:      DocType
    source_id:     Optional[str]
    uploaded_at:   date
    tx_count:      int
    total_amount:  float
    ocr_attempted: bool
    ocr_success:   bool

    model_config = {"from_attributes": True}



class IngestionResult(BaseModel):
    """
    Result returned after the ingestion of one or more files.

    Attributes:
        file_id:      ID of the file created in the database.
        filename:     Original file name.
        status:       "ok" | "partial" | "ocr_failed" | "no_parser"
        tx_count:     Number of transactions created.
        total_amount: Sum of extracted amounts.
        errors:       List of errors or warnings encountered.
    """

    file_id:      Optional[str]
    filename:     str
    status:       str
    tx_count:     int   = 0
    total_amount: float = 0.0
    errors:       list[str] = []