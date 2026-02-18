"""
PDF Renderer Module

Provides LaTeX template rendering functionality for PDF generation.
This module extracts and consolidates the rendering logic from the existing
TemplateGenerator class.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..utils.template_filters import latex_escape, proper_title


class PDFRenderer:
    """
    Handles LaTeX template rendering for PDF generation.

    This class provides a clean interface for rendering Jinja2 templates
    to LaTeX format, which can then be converted to PDF.
    """

    _ENV_CACHE: Dict[str, Environment] = {}

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize the PDF renderer.

        Args:
            template_dir: Path to the templates directory.
                        Defaults to templates/ in the parent directory.
        """
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent / "templates"

        self.template_dir = Path(template_dir)
        self._setup_environment()

    def _setup_environment(self) -> None:
        """Set up Jinja2 environment with caching."""
        cache_key = str(self.template_dir.resolve())
        if cache_key in self._ENV_CACHE:
            self.env = self._ENV_CACHE[cache_key]
        else:
            self.env = Environment(
                loader=FileSystemLoader(self.template_dir),
                autoescape=select_autoescape(),
                trim_blocks=True,
                lstrip_blocks=True,
            )
            # Add filters
            self.env.filters["latex_escape"] = latex_escape
            self.env.filters["proper_title"] = proper_title

            self._ENV_CACHE[cache_key] = self.env

    def render(
        self,
        template_name: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Render a LaTeX template with the given context.

        Args:
            template_name: Name of the Jinja2 template file
            context: Dictionary of template variables

        Returns:
            Rendered LaTeX content as string
        """
        template = self.env.get_template(template_name)
        return template.render(**context)

    def render_to_file(
        self,
        template_name: str,
        context: Dict[str, Any],
        output_path: Path,
    ) -> None:
        """
        Render a LaTeX template and save to file.

        Args:
            template_name: Name of the Jinja2 template file
            context: Dictionary of template variables
            output_path: Path to save the rendered LaTeX file
        """
        content = self.render(template_name, context)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

    def list_templates(self) -> list:
        """
        List available LaTeX templates.

        Returns:
            List of available template names
        """
        templates = []
        for template_file in self.template_dir.glob("*.j2"):
            # Filter to only LaTeX-related templates
            if "tex" in template_file.stem or "resume" in template_file.stem:
                templates.append(template_file.name)
        return templates
