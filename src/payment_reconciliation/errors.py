"""Custom exceptions for payment reconciliation."""


class ReconciliationError(Exception):
    """Base class for user-facing reconciliation errors."""


class InputFileError(ReconciliationError):
    """Raised when the input Excel file cannot be read."""


class ValidationError(ReconciliationError):
    """Raised when input data fails validation."""
