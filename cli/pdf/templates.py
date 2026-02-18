"""
Template Options Module

Provides template customization options for PDF generation.
This module defines configuration options for resume templates.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TemplateOptions:
    """
    Configuration options for resume templates.

    This class provides a structured way to customize template rendering
    options for PDF generation.
    """

    # Template style options
    style: str = "base"  # base, modern, minimalist, academic, tech

    # Font options
    font_family: Optional[str] = None  # e.g., "Times New Roman", "Latin Modern"
    font_size: int = 11  # Base font size in points

    # Layout options
    page_size: str = "letter"  # letter, a4, legal
    margin_top: float = 1.0  # inches
    margin_bottom: float = 1.0  # inches
    margin_left: float = 1.0  # inches
    margin_right: float = 1.0  # inches

    # Content options
    include_photo: bool = False
    photo_path: Optional[str] = None
    include_references: bool = False

    # Section options
    sections_order: Optional[List[str]] = None  # Custom section order

    # PDF-specific options
    pdf_title: Optional[str] = None
    pdf_author: Optional[str] = None
    pdf_subject: Optional[str] = None
    pdf_keywords: Optional[str] = None

    def __post_init__(self):
        """Validate options after initialization."""
        valid_styles = ["base", "modern", "minimalist", "academic", "tech"]
        if self.style not in valid_styles:
            raise ValueError(f"Invalid style: {self.style}. Must be one of {valid_styles}")

        valid_page_sizes = ["letter", "a4", "legal"]
        if self.page_size not in valid_page_sizes:
            raise ValueError(
                f"Invalid page_size: {self.page_size}. Must be one of {valid_page_sizes}"
            )

    def to_latex_options(self) -> dict:
        """
        Convert options to LaTeX-specific settings.

        Returns:
            Dictionary of LaTeX settings
        """
        options = {
            "font_size": self.font_size,
            "page_size": self.page_size,
            "margin_top": self.margin_top,
            "margin_bottom": self.margin_bottom,
            "margin_left": self.margin_left,
            "margin_right": self.margin_right,
        }

        if self.font_family:
            options["font_family"] = self.font_family

        return options

    @classmethod
    def modern(cls) -> "TemplateOptions":
        """Create options for modern style template."""
        return cls(style="modern", font_size=10)

    @classmethod
    def minimalist(cls) -> "TemplateOptions":
        """Create options for minimalist style template."""
        return cls(style="minimalist", font_size=11)

    @classmethod
    def academic(cls) -> "TemplateOptions":
        """Create options for academic style template."""
        return cls(style="academic", font_size=12, include_references=True)

    @classmethod
    def tech(cls) -> "TemplateOptions":
        """Create options for tech style template."""
        return cls(style="tech", font_size=10)


# Pre-defined template configurations
TEMPLATE_PRESETS = {
    "base": TemplateOptions(),
    "modern": TemplateOptions.modern(),
    "minimalist": TemplateOptions.minimalist(),
    "academic": TemplateOptions.academic(),
    "tech": TemplateOptions.tech(),
}


def get_template_preset(name: str) -> TemplateOptions:
    """
    Get a pre-defined template preset.

    Args:
        name: Name of the preset (base, modern, minimalist, academic, tech)

    Returns:
        TemplateOptions instance

    Raises:
        ValueError: If preset name is not found
    """
    if name not in TEMPLATE_PRESETS:
        raise ValueError(f"Unknown preset: {name}. Available: {list(TEMPLATE_PRESETS.keys())}")
    return TEMPLATE_PRESETS[name]
