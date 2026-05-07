"""
Orchestrates the full file ingestion pipeline:
    upload -> validate format -> save to disk -> parse -> persist transactions.

Single Responsibility: this service only coordinates. Each step
(parsing, categorization, storage) is delegated to the appropriate class.
"""

import logging
from datetime import date

from backend.core.enums import DocType, EntryMethod, FileType, SourceType
from backend.core.interfaces import (
    IActionRepository,
    IFileRepository,
    IParser,
    ISourceRepository,
    ITransactionRepository,
    IFileStorage,
)
from backend.core.models import PaymentSource, UploadedFile
from backend.infrastructure.parsers.txt_parser import TxtNotesParser
from backend.schemas.file import IngestionResult

logger = logging.getLogger(__name__)

_EXTENSION_TO_FILE_TYPE: dict[str, FileType] = {
    ".pdf":  FileType.PDF,
    ".xlsx": FileType.XLSX,
    ".png":  FileType.IMAGE,
    ".jpg":  FileType.IMAGE,
    ".jpeg": FileType.IMAGE,
    ".txt":  FileType.TXT,
}


class IngestionService:
    """
    Drives the complete file ingestion workflow.

    Args:
        parsers:          Ordered list of IParser implementations.
                          can_parse() is called in order; first match wins.
        transaction_repo: Repository for persisting transactions.
        source_repo:      Repository for payment sources.
        file_repo:        Repository for uploaded file metadata.
        action_repo:      Repository for action items (from notes.txt).
        storage:          File storage implementation.
    """

    def __init__(
        self,
        parsers:          list[IParser],
        transaction_repo: ITransactionRepository,
        source_repo:      ISourceRepository,
        file_repo:        IFileRepository,
        action_repo:      IActionRepository,
        storage:          IFileStorage,
    ) -> None:
        self._parsers          = parsers
        self._transaction_repo = transaction_repo
        self._source_repo      = source_repo
        self._file_repo        = file_repo
        self._action_repo      = action_repo
        self._storage          = storage

    def ingest(
        self,
        filename:     str,
        content:      bytes,
        doc_type:     DocType,
        source_label: str,
        source_type:  SourceType,
    ) -> IngestionResult:
        """
        Runs the full ingestion pipeline for a single file.

        Steps:
        1. Resolve or create the payment source.
        2. Save the file to disk.
        3. Create the UploadedFile record.
        4. Find a matching parser and extract transactions.
        5. Persist all transactions.
        6. For notes.txt, also extract and persist action items.
        7. Update file statistics (tx_count, total_amount).

        Args:
            filename:     Original name of the uploaded file.
            content:      Raw bytes of the file.
            doc_type:     Document type declared by the user.
            source_label: Human-readable label for the payment source.
            source_type:  Type of payment source.

        Returns:
            IngestionResult summarising what was created or what failed.
        """
        from pathlib import Path
        errors: list[str] = []

        # Step 1 — Resolve or create payment source
        source = self._source_repo.find_by_label(source_label)
        if not source:
            source = self._source_repo.save(PaymentSource(
                id=None,
                label=source_label,
                source_type=source_type,
                last_four=None,
                created_at=date.today(),
            ))
            logger.info("New payment source created: '%s'", source_label)

        # Step 2 — Persist file to disk
        storage_path = self._storage.save(filename, content)

        # Step 3 — Create UploadedFile record
        extension = Path(filename).suffix.lower()
        file_record = self._file_repo.save(UploadedFile(
            id=None,
            filename=filename,
            file_type=_EXTENSION_TO_FILE_TYPE.get(extension, FileType.TXT),
            doc_type=doc_type,
            storage_path=storage_path,
            source_id=source.id,
            uploaded_at=date.today(),
            ocr_attempted=False,
            ocr_success=False,
        ))

        # Step 4 — Find a matching parser
        matching_parser = next(
            (p for p in self._parsers if p.can_parse(filename)), None
        )
        if not matching_parser:
            logger.warning("No parser found for file: '%s'", filename)
            return IngestionResult(
                file_id=file_record.id,
                filename=filename,
                status="no_parser",
                errors=[f"No parser available for file type '{extension}'."],
            )

        # Step 5 — Parse and persist transactions
        transactions = matching_parser.parse(
            storage_path,
            source.id if source.id != None else "",
            file_record.id if file_record.id != None else "",
        )

        ocr_used    = isinstance(matching_parser, type) and hasattr(matching_parser, "ocr_confidence")
        saved_count = 0

        for transaction in transactions:
            try:
                self._transaction_repo.save(transaction)
                saved_count += 1
            except Exception as exc:
                error_msg = f"Failed to save transaction '{transaction.description}': {exc}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Step 6 — Extract action items from notes files
        if isinstance(matching_parser, TxtNotesParser):
            action_items = matching_parser.extract_action_items(storage_path, filename)
            for item in action_items:
                try:
                    self._action_repo.save(item)
                except Exception as exc:
                    errors.append(f"Failed to save action item: {exc}")

        # Step 7 — Update file statistics
        total_amount = sum(
            t.amount for t in transactions if t.amount > 0
        )
        self._file_repo.update_stats(
            file_record.id if file_record.id != None else "", 
            saved_count, 
            total_amount
        )

        status = "ok" if not errors else "partial"
        logger.info(
            "Ingestion complete for '%s': %d transactions, status=%s",
            filename, saved_count, status,
        )
        return IngestionResult(
            file_id=file_record.id,
            filename=filename,
            status=status,
            tx_count=saved_count,
            total_amount=round(total_amount, 2),
            errors=errors,
        )