"""
resume-pdf-lib - Shared Python library for PDF resume generation.

This library provides a unified interface for generating PDF resumes
using LaTeX templates. It can be used by both resume-cli and ResumeAI.

Usage:
    from resume_pdf_lib import PDFGenerator

    generator = PDFGenerator(templates_dir="/path/to/templates")
    pdf_bytes = generator.generate_pdf(resume_data, variant="modern")
"""

from .generator import PDFGenerator, latex_escape, proper_title, get_generator
from .exceptions import (
    PDFGenerationError,
    TemplateNotFoundError,
    InvalidVariantError,
    LaTeXCompilationError,
)

__version__ = "0.1.0"

__all__ = [
    "PDFGenerator",
    "latex_escape",
    "proper_title",
    "get_generator",
    "PDFGenerationError",
    "TemplateNotFoundError",
    "InvalidVariantError",
    "LaTeXCompilationError",
]
