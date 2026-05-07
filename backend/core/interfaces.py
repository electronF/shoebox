"""
Abstract domain interfaces (ABC).

Each interface defines a contract that concrete implementations
(infrastructure layer) must fulfill. Services depend solely on these
interfaces (DIP), never on concrete classes.

ISP Principle applied: one interface per distinct responsibility.
"""

from abc import ABC, abstractmethod
from typing import Optional

from .models import (
    ActionItem,
    Anomaly,
    Invoice,
    PaymentSource,
    Transaction,
    UploadedFile,
)


class ITransactionRepository(ABC):
    """Persistence contract for transactions."""

    @abstractmethod
    def save(self, transaction: Transaction) -> Transaction:
        """Persists a transaction and returns the instance with its ID."""
        ...

    @abstractmethod
    def get_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """Returns a transaction by its ID, or None if non-existent."""
        ...

    @abstractmethod
    def get_all(
        self,
        source_id: Optional[str] = None,
        exclude_personal: bool = False,
    ) -> list[Transaction]:
        """
        Returns all transactions with optional filters.

        Args:
            source_id: Filter by payment source if provided.
            exclude_personal: Excludes personal expenses if True.
        """
        ...

    @abstractmethod
    def get_by_file(self, file_id: str) -> list[Transaction]:
        """Returns all transactions extracted from a given file."""
        ...

    @abstractmethod
    def update(self, transaction: Transaction) -> Transaction:
        """Updates an existing transaction."""
        ...

    @abstractmethod
    def delete(self, transaction_id: str) -> bool:
        """Deletes a transaction. Returns True if found and deleted."""
        ...


class IInvoiceRepository(ABC):
    """Persistence contract for issued invoices."""

    @abstractmethod
    def save(self, invoice: Invoice) -> Invoice: ...

    @abstractmethod
    def get_by_id(self, invoice_id: str) -> Optional[Invoice]: ...

    @abstractmethod
    def get_all(self, status: Optional[str] = None) -> list[Invoice]: ...

    @abstractmethod
    def update(self, invoice: Invoice) -> Invoice: ...


class ISourceRepository(ABC):
    """Persistence contract for payment sources."""

    @abstractmethod
    def save(self, source: PaymentSource) -> PaymentSource: ...

    @abstractmethod
    def get_all(self) -> list[PaymentSource]: ...

    @abstractmethod
    def find_by_label(self, label: str) -> Optional[PaymentSource]: ...

    @abstractmethod
    def find_by_id(self, source_id: str) -> Optional[PaymentSource]:
        """Returns the source matching the given ID, or None."""
        ...


class IFileRepository(ABC):
    """Persistence contract for uploaded files."""

    @abstractmethod
    def save(self, uploaded_file: UploadedFile) -> UploadedFile: ...

    @abstractmethod
    def get_all(self) -> list[UploadedFile]: ...

    @abstractmethod
    def update_stats(
        self,
        file_id: str,
        tx_count: int,
        total_amount: float,
    ) -> None:
        """Updates aggregated file statistics after ingestion."""
        ...
    
    @abstractmethod
    def update_ocr_status(
        self,
        file_id:       str,
        ocr_attempted: bool,
        ocr_success:   bool,
    ) -> None: ...


class IAnomalyRepository(ABC):
    """Persistence contract for anomalies."""

    @abstractmethod
    def save(self, anomaly: Anomaly) -> Anomaly: ...

    @abstractmethod
    def get_unresolved(self) -> list[Anomaly]: ...

    @abstractmethod
    def mark_resolved(self, anomaly_id: str) -> bool: ...


class IActionRepository(ABC):
    """Persistence contract for action items / tasks."""

    @abstractmethod
    def save(self, action: ActionItem) -> ActionItem: ...

    @abstractmethod
    def get_all(self, status: Optional[str] = None) -> list[ActionItem]: ...

    @abstractmethod
    def update_status(self, action_id: str, status: str) -> bool: ...


class IParser(ABC):
    """
    Interface for all file parsers.

    OCP Principle: adding support for a new format
    = create a new subclass, without modifying existing code.
    """

    @abstractmethod
    def can_parse(self, filename: str) -> bool:
        """
        Indicates if this parser supports the given file.

        Args:
            filename: File name (with extension).

        Returns:
            True if this parser can process this file type.
        """
        ...

    @abstractmethod
    def parse(
        self,
        file_path: str,
        source_id: str,
        file_id: str,
    ) -> list[Transaction]:
        """
        Parses a file and returns extracted transactions.

        Args:
            file_path: Absolute path to the file on disk.
            source_id: ID of the associated payment source.
            file_id:   ID of the uploaded file (for traceability).

        Returns:
            List of extracted transactions. May be empty if the
            file does not contain transactional data (e.g., notes.txt).
        """
        ...
        
    @property
    def produces_ocr(self) -> bool:
        """Returns True if this parser uses OCR to extract data."""
        return False


class IFileStorage(ABC):
    """Interface for physical persistence of uploaded files."""

    @abstractmethod
    def save(self, filename: str, content: bytes) -> str:
        """
        Saves a file and returns its storage path.

        Args:
            filename: Original file name.
            content:  Binary content of the file.

        Returns:
            Absolute path of the saved file.
        """
        ...

    @abstractmethod
    def exists(self, storage_path: str) -> bool:
        """Checks if a file exists at the given location."""
        ...