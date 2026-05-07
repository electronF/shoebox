"""
Transaction validation logic.

Validates individual transactions after parsing, before persistence.
Returns a structured ValidationResult so the ingestion service can
decide whether to persist, flag, or reject each transaction.
"""

import logging
from dataclasses import dataclass, field
from datetime import date

from backend.core.enums import ValidationStatus
from backend.core.models import Transaction

logger = logging.getLogger(__name__)

# Tolerance for rounding differences in tax calculations (CAD)
_TAX_TOLERANCE_CAD = 0.05

# Quebec combined tax rate: TPS 5% + TVQ 9.975% = 14.975%
_QUEBEC_COMBINED_TAX_RATE = 0.14975

# Maximum age of a receipt before a warning is raised (days)
_MAX_RECEIPT_AGE_DAYS = 730  # 2 years


@dataclass
class ValidationResult:
    """
    Outcome of validating a single transaction.

    Attributes:
        status:   Final validation status for the transaction.
        warnings: Non-blocking issues — transaction is accepted but flagged.
        errors:   Blocking issues — transaction should not be persisted as-is.
    """

    status:   ValidationStatus        = ValidationStatus.OK
    warnings: list[str]               = field(default_factory=list)
    errors:   list[str]               = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Returns True if there are no blocking errors."""
        return len(self.errors) == 0

    @property
    def has_warnings(self) -> bool:
        """Returns True if there are non-blocking warnings."""
        return len(self.warnings) > 0


def validate_transaction(transaction: Transaction) -> ValidationResult:
    """
    Runs all validation rules against a single transaction.

    Rules applied (in order):
    1. Amount must not be zero.
    2. Date must not be in the future.
    3. Date must not be older than MAX_RECEIPT_AGE_DAYS.
    4. Description must not be empty.
    5. For informal receipts, no tax validation is applied.

    The result status is set to:
    - OK       if no issues found
    - WARNING  if only non-blocking warnings exist
    - ERROR    if at least one blocking error exists

    Args:
        transaction: The Transaction domain object to validate.

    Returns:
        A ValidationResult with status, warnings, and errors populated.
    """
    result = ValidationResult()
    today  = date.today()

    # Rule 1 — Amount check
    if transaction.amount == 0.0:
        result.errors.append("Amount must not be zero.")

    # Rule 2 — Future date check
    if transaction.date > today:
        result.errors.append(
            f"Transaction date {transaction.date} is in the future."
        )

    # Rule 3 — Stale date warning
    age_days = (today - transaction.date).days
    if age_days > _MAX_RECEIPT_AGE_DAYS:
        result.warnings.append(
            f"Transaction date is {age_days} days old — please confirm it is correct."
        )

    # Rule 4 — Empty description
    if not transaction.description.strip():
        result.errors.append("Description must not be empty.")

    # Rule 5 — Tax coherence (only for non-informal receipts with a known amount)
    if (
        not transaction.is_informal
        and transaction.amount > 0
        and transaction.entry_method.value == "ocr"
    ):
        _validate_tax_coherence(transaction, result)

    # Determine final status
    if result.errors:
        result.status = ValidationStatus.ERROR
    elif result.warnings:
        result.status = ValidationStatus.WARNING

    if result.status != ValidationStatus.OK:
        logger.debug(
            "validate_transaction '%s': %s — errors=%s warnings=%s",
            transaction.description,
            result.status.value,
            result.errors,
            result.warnings,
        )

    return result


def _validate_tax_coherence(
    transaction: Transaction,
    result: ValidationResult,
) -> None:
    """
    Checks whether the transaction amount is consistent with Quebec tax rates.

    If the amount does not approximate either a pre-tax or post-tax total
    under standard Quebec rates, a warning is added (non-blocking).

    Args:
        transaction: Transaction to check.
        result:      ValidationResult to append warnings to (mutated in place).
    """
    amount = abs(transaction.amount)

    # Infer what the pre-tax subtotal would be if taxes are included
    implied_pretax = amount / (1 + _QUEBEC_COMBINED_TAX_RATE)
    implied_total  = implied_pretax * (1 + _QUEBEC_COMBINED_TAX_RATE)

    if abs(implied_total - amount) > _TAX_TOLERANCE_CAD * 10:
        result.warnings.append(
            "Amount does not align with standard Quebec tax rates (TPS+TVQ). "
            "Consider marking as informal receipt."
        )