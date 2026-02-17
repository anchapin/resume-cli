"""
PDF Generation Module

This module provides a shared PDF generation infrastructure for resume-cli,
extracting the PDF generation logic into a reusable module.

Components:
- renderer.py: LaTeX template rendering logic
- converter.py: PDF conversion utilities
- templates.py: Template customization options

This module serves as a foundation for a future shared package (resume-pdf-lib)
that can be used by both resume-cli and ResumeAI.
"""

from .converter import PDFConverter
from .renderer import PDFRenderer
from .templates import TemplateOptions

__all__ = ["PDFRenderer", "PDFConverter", "TemplateOptions"]
