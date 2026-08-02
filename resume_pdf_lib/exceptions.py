"""
Custom exceptions for resume-pdf-lib.
"""


class PDFGenerationError(Exception):
    """Base exception for PDF generation errors."""



class TemplateNotFoundError(PDFGenerationError):
    """Raised when a template file is not found."""



class InvalidVariantError(PDFGenerationError):
    """Raised when an invalid variant name is provided."""



class LaTeXCompilationError(PDFGenerationError):
    """Raised when LaTeX compilation fails."""



class ValidationError(PDFGenerationError):
    """Raised when resume data validation fails."""

