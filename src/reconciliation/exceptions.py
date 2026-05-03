"""Custom exceptions for reconciliation parsing and comparison."""


class ReconciliationError(Exception):
    """Base exception for the reconciliation library."""


class UnsupportedFileTypeError(ReconciliationError):
    """Raised when a provided document has an unsupported file extension."""


class ParsingError(ReconciliationError):
    """Raised when a supported document cannot be parsed safely."""
