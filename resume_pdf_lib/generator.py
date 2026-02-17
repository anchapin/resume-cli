"""
PDF Generator for resumes using LaTeX templates.

This module provides a unified interface for generating PDF resumes
from structured data using Jinja2 templates and LaTeX.
"""

import logging
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from .exceptions import (
    InvalidVariantError,
    LaTeXCompilationError,
    TemplateNotFoundError,
    ValidationError,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFGenerator:
    """
    Generate PDF resumes from structured data using LaTeX templates.

    This class provides a unified interface for PDF generation that can be
    used by both resume-cli and ResumeAI applications.
    """

    _env_cache: Dict[str, "Environment"] = {}

    def __init__(
        self,
        templates_dir: Optional[str] = None,
        default_variant: str = "base",
        latex_compiler: str = "xelatex",
        compilation_timeout: int = 30,
    ):
        """Initialize the PDF generator."""
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            self.templates_dir = Path(__file__).parent / "templates"

        self.default_variant = default_variant
        self.latex_compiler = latex_compiler
        self.compilation_timeout = compilation_timeout

        self._validate_templates_dir()
        self._setup_jinja2()

    def _validate_templates_dir(self) -> None:
        """Ensure the templates directory exists."""
        if not self.templates_dir.exists():
            raise TemplateNotFoundError(
                f"Templates directory not found: {self.templates_dir}"
            )
        logger.info(f"Templates directory: {self.templates_dir}")

    def _setup_jinja2(self) -> None:
        """Set up Jinja2 environment for LaTeX templating."""
        cache_key = str(self.templates_dir.resolve())

        if cache_key in self._env_cache:
            self.jinja_env = self._env_cache[cache_key]
            return

        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(["tex"]),
            block_start_string="\\BLOCK{",
            block_end_string="}",
            variable_start_string="\\VAR{",
            variable_end_string="}",
            comment_start_string="\\#{",
            comment_end_string="}",
            line_statement_prefix="%%",
            line_comment_prefix="%#",
            trim_blocks=True,
            lstrip_blocks=True,
        )

        self.jinja_env.filters["latex_escape"] = latex_escape
        self.jinja_env.filters["proper_title"] = proper_title

        self.jinja_env.finalize = lambda x: (
            latex_escape(x)
            if isinstance(x, str) and not isinstance(x, Markup)
            else x
        )

        self._env_cache[cache_key] = self.jinja_env

    def generate_pdf(
        self,
        resume_data: Dict[str, Any],
        variant: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> bytes:
        """Generate a PDF resume from structured data."""
        variant = variant or self.default_variant

        if not re.match(r"^[a-zA-Z0-9_-]+$", variant):
            raise InvalidVariantError(
                f"Invalid variant name: '{variant}'. "
                "Variant name must contain only letters, numbers, hyphens, and underscores."
            )

        variant_dir = self.templates_dir / variant
        has_variant_dir = variant_dir.exists() and variant_dir.is_dir()

        single_template = self.templates_dir / f"resume_{variant}.tex"
        has_single_template = single_template.exists()

        if not has_variant_dir and not has_single_template:
            available = self.list_variants()
            raise InvalidVariantError(
                f"Variant '{variant}' not found. "
                f"Available variants: {available}"
            )

        normalized_data = self._normalize_resume_data(resume_data)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            try:
                if has_variant_dir:
                    rendered_tex = self._render_variant_template(variant, normalized_data)
                else:
                    rendered_tex = self._render_single_template(variant, normalized_data)

                tex_file = temp_path / "resume.tex"
                tex_file.write_text(rendered_tex, encoding="utf-8")

                self._compile_latex(tex_file)

                pdf_file = temp_path / "resume.pdf"
                if not pdf_file.exists():
                    raise LaTeXCompilationError("PDF was not generated")

                pdf_bytes = pdf_file.read_bytes()
                logger.info(f"Generated PDF ({len(pdf_bytes)} bytes)")

                if output_path:
                    output = Path(output_path)
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_bytes(pdf_bytes)
                    logger.info(f"Saved PDF to: {output_path}")
                    return None

                return pdf_bytes

            except (LaTeXCompilationError, TemplateNotFoundError, InvalidVariantError):
                raise
            except Exception as e:
                logger.error(f"PDF generation error: {e}")
                raise LaTeXCompilationError(f"PDF generation failed: {e}")

    def _render_variant_template(self, variant: str, resume_data: Dict[str, Any]) -> str:
        """Render a variant-style template (ResumeAI style)."""
        template_file = self.templates_dir / variant / "main.tex"
        if not template_file.exists():
            raise TemplateNotFoundError(
                f"Template file 'main.tex' not found in variant '{variant}'"
            )

        template = self.jinja_env.get_template(f"{variant}/main.tex")
        return template.render(resume=resume_data)

    def _render_single_template(self, variant: str, resume_data: Dict[str, Any]) -> str:
        """Render a single-file template (resume-cli style)."""
        context = self._prepare_template_context(resume_data)
        context["variant"] = variant

        template_name = f"resume_{variant}.tex"
        try:
            template = self.jinja_env.get_template(template_name)
        except Exception:
            template = self.jinja_env.get_template("resume_tex.j2")

        return template.render(**context)

    def _prepare_template_context(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare template context from resume data."""
        context = {}

        if "basics" in resume_data:
            context["contact"] = resume_data["basics"]
            context["summary"] = resume_data["basics"].get("summary", "")
        else:
            context["contact"] = resume_data.get("contact", {})
            context["summary"] = resume_data.get("summary", "")

        context["experience"] = resume_data.get("work", resume_data.get("experience", []))
        context["education"] = resume_data.get("education", [])
        context["skills"] = resume_data.get("skills", {})
        context["projects"] = resume_data.get("projects", [])
        context["publications"] = resume_data.get("publications", [])
        context["certifications"] = resume_data.get("certifications", [])
        context["affiliations"] = resume_data.get("affiliations", [])

        return context

    def _normalize_resume_data(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize resume data to a consistent format."""
        if not resume_data:
            resume_data = {}

        if "basics" not in resume_data:
            basics = {}
            if "contact" in resume_data:
                contact = resume_data["contact"]
                basics = {
                    "name": contact.get("name", "Your Name"),
                    "label": contact.get("title", "Professional Title"),
                    "email": contact.get("email", "email@example.com"),
                    "phone": contact.get("phone", "+1 234 567 8900"),
                    "url": contact.get("url", ""),
                    "summary": resume_data.get("summary", ""),
                }
                if "location" in contact:
                    location = contact["location"]
                    basics["location"] = {
                        "address": location.get("address", ""),
                        "city": location.get("city", ""),
                        "region": location.get("state", ""),
                        "postalCode": location.get("zip", ""),
                        "country": location.get("country", ""),
                    }
            resume_data["basics"] = basics

        for key in ["work", "education", "skills", "projects", "awards", "certificates", "publications"]:
            if key not in resume_data:
                resume_data[key] = []

        for job in resume_data.get("work", []):
            if "startDate" not in job and "start_date" in job:
                job["startDate"] = job["start_date"]
            if "endDate" not in job and "end_date" in job:
                job["endDate"] = job["end_date"]
            if "highlights" not in job and "bullets" in job:
                job["highlights"] = job["bullets"]

        return resume_data

    def _compile_latex(self, tex_file: Path) -> None:
        """Compile a LaTeX file to PDF."""
        output_dir = tex_file.parent
        tex_stem = tex_file.stem

        compiler_path = shutil.which(self.latex_compiler)
        if not compiler_path:
            if self.latex_compiler == "xelatex":
                self.latex_compiler = "pdflatex"
                compiler_path = shutil.which(self.latex_compiler)
                if not compiler_path:
                    raise LaTeXCompilationError(
                        f"LaTeX compiler '{self.latex_compiler}' not found. "
                        "Please install TeX Live or MacTeX."
                    )
            else:
                raise LaTeXCompilationError(
                    f"LaTeX compiler '{self.latex_compiler}' not found. "
                    "Please install TeX Live or MacTeX."
                )

        for attempt in range(2):
            result = subprocess.run(
                [
                    self.latex_compiler,
                    "-interaction=nonstopmode",
                    "-output-directory",
                    str(output_dir),
                    str(tex_file.name),
                ],
                cwd=str(output_dir),
                capture_output=True,
                text=True,
                timeout=self.compilation_timeout,
            )

            pdf_file = output_dir / f"{tex_stem}.pdf"

            if not pdf_file.exists():
                logger.error(f"LaTeX run {attempt + 1} failed - no PDF generated")
                raise LaTeXCompilationError(
                    f"LaTeX compilation failed (exit code: {result.returncode}). "
                    "PDF was not generated."
                )

            if result.returncode != 0:
                logger.warning(
                    f"LaTeX run {attempt + 1} completed with warnings "
                    f"(exit code: {result.returncode})"
                )

        logger.info(f"Successfully compiled {tex_file.name}")

    def list_variants(self) -> List[str]:
        """List available template variants."""
        variants = []

        for item in self.templates_dir.iterdir():
            if item.is_dir() and (item / "main.tex").exists():
                variants.append(item.name)

        for template_file in self.templates_dir.glob("resume_*.tex"):
            variant_name = template_file.stem.replace("resume_", "")
            if variant_name not in variants:
                variants.append(variant_name)

        return sorted(variants)

    def generate_markdown(
        self,
        resume_data: Dict[str, Any],
        variant: str = "base",
    ) -> str:
        """Generate a Markdown resume."""
        normalized_data = self._normalize_resume_data(resume_data)
        context = self._prepare_template_context(normalized_data)
        context["variant"] = variant

        template_name = f"resume_{variant}_md.j2"
        try:
            template = self.jinja_env.get_template(template_name)
        except Exception:
            template_name = "resume_md.j2"
            try:
                template = self.jinja_env.get_template(template_name)
            except Exception:
                raise TemplateNotFoundError(
                    f"Markdown template not found for variant '{variant}'"
                )

        return template.render(**context)


def latex_escape(text: Any) -> Markup:
    """Escape special LaTeX characters in text."""
    if text is None:
        return Markup("")

    if isinstance(text, Markup):
        return text

    text_str = str(text)
    result = []

    for char in text_str:
        if char == "\\":
            result.append(r"\textbackslash{}")
        elif char in "&%$#_{}~^<>":
            escaped_map = {
                "&": r"\&", "%": r"\%", "$": r"\$",
                "#": r"\#", "_": r"\_", "{": r"\{",
                "}": r"\}", "~": r"\textasciitilde{}",
                "^": r"\^{}", "<": r"\textless{}",
                ">": r"\textgreater{}",
            }
            result.append(escaped_map[char])
        else:
            result.append(char)

    return Markup("".join(result))


def proper_title(text: str) -> str:
    """Convert text to proper title case."""
    if not text:
        return text

    small_words = {
        "a", "an", "the", "and", "but", "or", "for", "nor",
        "on", "at", "to", "from", "by", "in", "of", "with", "without",
    }

    words = text.split()
    result = []

    for i, word in enumerate(words):
        if i == 0:
            result.append(word.capitalize())
        elif word.lower() in small_words:
            result.append(word.lower())
        else:
            result.append(word.capitalize())

    return " ".join(result)


_default_generator: Optional[PDFGenerator] = None


def get_generator(templates_dir: Optional[str] = None) -> PDFGenerator:
    """Get or create a default PDFGenerator instance."""
    global _default_generator

    if _default_generator is None or templates_dir is not None:
        _default_generator = PDFGenerator(templates_dir=templates_dir)

    return _default_generator
