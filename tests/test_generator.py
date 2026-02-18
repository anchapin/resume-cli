"""
Tests for resume-pdf-lib.
"""

import pytest
from pathlib import Path
import tempfile

from resume_pdf_lib import (
    PDFGenerator,
    latex_escape,
    proper_title,
    TemplateNotFoundError,
    InvalidVariantError,
    LaTeXCompilationError,
)
from markupsafe import Markup


class TestLatexEscape:
    """Tests for latex_escape function."""

    def test_escape_ampersand(self):
        """Test ampersand escaping."""
        assert latex_escape("A & B") == Markup(r"A \& B")

    def test_escape_percent(self):
        """Test percent escaping."""
        assert latex_escape("100%") == Markup(r"100\%")

    def test_escape_dollar(self):
        """Test dollar sign escaping."""
        assert latex_escape("$100") == Markup(r"\$100")

    def test_escape_hash(self):
        """Test hash escaping."""
        assert latex_escape("#1") == Markup(r"\#1")

    def test_escape_underscore(self):
        """Test underscore escaping."""
        assert latex_escape("variable_name") == Markup(r"variable\_name")

    def test_escape_braces(self):
        """Test brace escaping."""
        assert latex_escape("{key}") == Markup(r"\{key\}")

    def test_escape_tilde(self):
        """Test tilde escaping."""
        assert latex_escape("~user") == Markup(r"\textasciitilde{}user")

    def test_escape_caret(self):
        """Test caret escaping."""
        assert latex_escape("x^2") == Markup(r"x\^{}2")

    def test_escape_less_than(self):
        """Test less than escaping."""
        assert latex_escape("a < b") == Markup(r"a \textless{} b")

    def test_escape_greater_than(self):
        """Test greater than escaping."""
        assert latex_escape("b > a") == Markup(r"b \textgreater{} a")

    def test_escape_backslash(self):
        """Test backslash escaping."""
        assert latex_escape(r"path\to\file") == Markup(
            r"path\textbackslash{}to\textbackslash{}file"
        )

    def test_none_input(self):
        """Test None input returns empty Markup."""
        assert latex_escape(None) == Markup("")

    def test_markup_input_unchanged(self):
        """Test Markup input is returned unchanged."""
        original = Markup("<b>bold</b>")
        assert latex_escape(original) == original


class TestProperTitle:
    """Tests for proper_title function."""

    def test_basic_title(self):
        """Test basic title case conversion."""
        assert proper_title("hello world") == "Hello World"

    def test_small_words_lowercase(self):
        """Test small words remain lowercase."""
        assert proper_title("the and of") == "The and of"

    def test_all_small_words(self):
        """Test string with only small words."""
        assert proper_title("the and of") == "The and of"

    def test_first_word_capitalized(self):
        """Test first word is always capitalized."""
        assert proper_title("a story") == "A Story"

    def test_empty_string(self):
        """Test empty string returns empty."""
        assert proper_title("") == ""

    def test_none_input(self):
        """Test None returns None."""
        assert proper_title(None) is None


class TestPDFGenerator:
    """Tests for PDFGenerator class."""

    @pytest.fixture
    def templates_dir(self):
        """Create a temporary directory with test templates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_path = Path(tmpdir)

            # Create a simple template
            template_dir = templates_path / "base"
            template_dir.mkdir()
            template_file = template_dir / "main.tex"
            template_file.write_text(r"""\documentclass{article}
\begin{document}
Hello \VAR{resume.basics.name}!
\end{document}""")

            yield str(templates_path)

    @pytest.fixture
    def resume_data(self):
        """Sample resume data."""
        return {
            "basics": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1 234 567 8900",
            },
            "work": [],
            "education": [],
            "skills": [],
            "projects": [],
        }

    def test_init_with_valid_templates_dir(self, templates_dir):
        """Test initialization with valid templates directory."""
        generator = PDFGenerator(templates_dir=templates_dir)
        assert generator.templates_dir.exists()

    def test_init_with_invalid_templates_dir(self):
        """Test initialization with invalid templates directory."""
        with pytest.raises(TemplateNotFoundError):
            PDFGenerator(templates_dir="/nonexistent/path")

    def test_list_variants(self, templates_dir):
        """Test listing available variants."""
        generator = PDFGenerator(templates_dir=templates_dir)
        variants = generator.list_variants()
        assert "base" in variants

    def test_normalize_resume_data_empty(self):
        """Test normalizing empty resume data."""
        generator = PDFGenerator(templates_dir=None)
        result = generator._normalize_resume_data({})
        assert "basics" in result

    def test_normalize_resume_data_with_basics(self, resume_data):
        """Test normalizing data that already has basics."""
        generator = PDFGenerator(templates_dir=None)
        result = generator._normalize_resume_data(resume_data)
        assert result["basics"]["name"] == "John Doe"

    def test_invalid_variant_raises_error(self, templates_dir, resume_data):
        """Test that invalid variant raises InvalidVariantError."""
        generator = PDFGenerator(templates_dir=templates_dir)
        with pytest.raises(InvalidVariantError):
            generator.generate_pdf(resume_data, variant="nonexistent")

    def test_variant_name_validation(self, templates_dir, resume_data):
        """Test that invalid variant names are rejected."""
        generator = PDFGenerator(templates_dir=templates_dir)
        with pytest.raises(InvalidVariantError):
            generator.generate_pdf(resume_data, variant="../etc/passwd")

    def test_generate_pdf_requires_latex(self, templates_dir, resume_data):
        """Test that PDF generation requires LaTeX compiler."""
        generator = PDFGenerator(templates_dir=templates_dir, latex_compiler="nonexistent")
        with pytest.raises(LaTeXCompilationError):
            generator.generate_pdf(resume_data, variant="base")


class TestGetGenerator:
    """Tests for get_generator convenience function."""

    def test_get_generator_creates_instance(self):
        """Test that get_generator creates a new instance."""
        from resume_pdf_lib import get_generator

        generator = get_generator()
        assert isinstance(generator, PDFGenerator)

    def test_get_generator_reuses_instance(self):
        """Test that get_generator reuses the default instance."""
        from resume_pdf_lib import get_generator

        gen1 = get_generator()
        gen2 = get_generator()
        assert gen1 is gen2

    def test_get_generator_with_custom_templates(self):
        """Test that get_generator creates new instance with custom templates."""
        from resume_pdf_lib import get_generator

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a minimal templates dir
            templates_path = Path(tmpdir) / "templates"
            templates_path.mkdir()

            gen = get_generator(templates_dir=str(templates_path))
            assert gen.templates_dir == templates_path


class TestExceptions:
    """Tests for custom exceptions."""

    def test_pdf_generation_error(self):
        """Test PDFGenerationError can be raised and caught."""
        from resume_pdf_lib import PDFGenerationError

        with pytest.raises(PDFGenerationError):
            raise PDFGenerationError("test error")

    def test_exception_inheritance(self):
        """Test exception inheritance hierarchy."""
        from resume_pdf_lib import (
            PDFGenerationError,
            TemplateNotFoundError,
            InvalidVariantError,
            LaTeXCompilationError,
        )

        assert issubclass(TemplateNotFoundError, PDFGenerationError)
        assert issubclass(InvalidVariantError, PDFGenerationError)
        assert issubclass(LaTeXCompilationError, PDFGenerationError)
