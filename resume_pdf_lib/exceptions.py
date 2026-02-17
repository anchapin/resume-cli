"""
Custom exceptions for resume-pdf-lib.
"""


class PDFGenerationError(Exception):
    """Base exception for PDF generation errors."""
    pass


class TemplateNotFoundError(PDFGenerationError):
    """Raised when a template file is not found."""
    pass


class InvalidVariantError(PDFGenerationError):
    """Raised when an invalid variant name is provided."""
    pass


class LaTeXCompilationError(PDFGenerationError):
    """Raised when LaTeX compilation fails."""
    pass


class ValidationError(PDFGenerationError):
    """Raised when resume data validation fails."""
    pass
