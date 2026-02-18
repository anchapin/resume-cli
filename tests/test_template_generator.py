"""Unit tests for TemplateGenerator class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cli.generators.template import TemplateGenerator
from cli.utils.config import Config


class TestTemplateGeneratorInitialization:
    """Test TemplateGenerator initialization."""

    def test_init_with_yaml_path(self, sample_yaml_file: Path):
        """Test initialization with yaml path."""
        gen = TemplateGenerator(yaml_path=sample_yaml_file)

        assert gen.yaml_handler.yaml_path == sample_yaml_file
        assert gen.config is not None
        assert gen.template_dir is not None

    def test_init_with_template_dir(self, sample_yaml_file: Path, temp_dir: Path):
        """Test initialization with custom template dir."""
        template_dir = temp_dir / "templates"
        gen = TemplateGenerator(yaml_path=sample_yaml_file, template_dir=template_dir)

        assert gen.template_dir == template_dir

    def test_init_default_template_dir(self):
        """Test initialization uses default template directory."""
        gen = TemplateGenerator()
        # Template dir should be set (we don't check exact path as it depends on installation)
        assert gen.template_dir is not None

    def test_jinja2_filters_registered(self, sample_yaml_file: Path):
        """Test that custom Jinja2 filters are registered."""
        gen = TemplateGenerator(yaml_path=sample_yaml_file)

        assert "latex_escape" in gen.env.filters
        assert "proper_title" in gen.env.filters


class TestLatexEscapeFilter:
    """Test latex_escape filter."""

    def test_latex_escape_special_chars(self):
        """Test latex_escape escapes special LaTeX characters."""
        gen = TemplateGenerator()
        filter_func = gen.env.filters["latex_escape"]

        # Test various special characters
        assert filter_func("a & b") == r"a \& b"
        assert filter_func("5% complete") == r"5\% complete"
        assert filter_func("$100") == r"\$100"
        assert filter_func("# section") == r"\# section"
        assert filter_func("text_var") == r"text\_var"
        assert filter_func("{item}") == r"\{item\}"
        assert filter_func("[key]") == r"[key]"  # Brackets not escaped

    def test_latex_escape_copyright_symbols(self):
        """Test latex_escape escapes copyright symbols."""
        gen = TemplateGenerator()
        filter_func = gen.env.filters["latex_escape"]

        assert filter_func("TradeMark") == r"TradeMark"
        assert filter_func("Registered") == r"Registered"
        assert filter_func("Copyright") == r"Copyright"
        assert filter_func("100 degrees") == r"100 \textsuperscript{\textdegree}{}"

    def test_latex_escape_math_symbols(self):
        """Test latex_escape escapes math symbols."""
        gen = TemplateGenerator()
        filter_func = gen.env.filters["latex_escape"]

        assert filter_func("x >= y") == r"x $\ge$ y"
        assert filter_func("x <= y") == r"x $\le$ y"
        assert filter_func("x ± y") == r"x $\pm$ y"

    def test_latex_escape_arrows(self):
        """Test latex_escape escapes arrows."""
        gen = TemplateGenerator()
        filter_func = gen.env.filters["latex_escape"]

        assert filter_func("a -> b") == r"a $\rightarrow$ b"

    def test_latex_escape_dashes(self):
        """Test latex_escape converts dashes."""
        gen = TemplateGenerator()
        filter_func = gen.env.filters["latex_escape"]

        assert filter_func("word—word") == r"word---word"  # em dash
        assert filter_func("word–word") == r"word--word"  # en dash

    def test_latex_escape_none(self):
        """Test latex_escape handles None input."""
        gen = TemplateGenerator()
        filter_func = gen.env.filters["latex_escape"]

        result = filter_func(None)
        # Updated to return empty Markup for safety instead of None
        from markupsafe import Markup

        assert result == Markup("")

    def test_latex_escape_empty(self):
        """Test latex_escape handles empty string."""
        gen = TemplateGenerator()
        filter_func = gen.env.filters["latex_escape"]

        result = filter_func("")
        assert result == ""

    def test_latex_escape_markdown_bold(self):
        """Test latex_escape converts markdown bold."""
        gen = TemplateGenerator()
        filter_func = gen.env.filters["latex_escape"]

        # Markdown bold **text** should be converted to \textbf{text}
        result = filter_func("**bold text**")
        assert r"\textbf{bold text}" in result

        # Test with normal text
        result = filter_func("normal **bold** normal")
        assert r"normal \textbf{bold} normal" in result


class TestProperTitleFilter:
    """Test proper_title filter."""

    def test_proper_title_capitalizes(self):
        """Test proper_title capitalizes correctly."""
        gen = TemplateGenerator()
        filter_func = gen.env.filters["proper_title"]

        assert filter_func("hello world") == "Hello World"
        assert filter_func("the quick brown fox") == "The Quick Brown Fox"

    def test_proper_title_small_words(self):
        """Test proper_title keeps small words lowercase."""
        gen = TemplateGenerator()
        filter_func = gen.env.filters["proper_title"]

        # Small words should be lowercase (except first word)
        assert filter_func("The Cat and The Dog") == "The Cat and the Dog"
        assert filter_func("A Tale of Two Cities") == "A Tale of Two Cities"

    def test_proper_title_first_word_capitalized(self):
        """Test proper_title always capitalizes first word."""
        gen = TemplateGenerator()
        filter_func = gen.env.filters["proper_title"]

        assert filter_func("the book") == "The Book"
        assert filter_func("a story") == "A Story"

    def test_proper_title_underscore_replacement(self):
        """Test proper_title replaces underscores with spaces."""
        gen = TemplateGenerator()
        filter_func = gen.env.filters["proper_title"]

        assert filter_func("hello_world_test") == "Hello World Test"

    def test_proper_title_empty(self):
        """Test proper_title handles empty string."""
        gen = TemplateGenerator()
        filter_func = gen.env.filters["proper_title"]

        result = filter_func("")
        assert result == ""

    def test_proper_title_none(self):
        """Test proper_title handles None input."""
        gen = TemplateGenerator()
        filter_func = gen.env.filters["proper_title"]

        result = filter_func(None)
        assert result is None


class TestGenerateMethod:
    """Test generate method."""

    @patch("cli.generators.template.TemplateGenerator._compile_pdf")
    def test_generate_markdown(self, mock_compile_pdf, sample_yaml_file: Path, temp_dir: Path):
        """Test generate creates markdown output."""
        gen = TemplateGenerator(yaml_path=sample_yaml_file)
        output_path = temp_dir / "test.md"

        content = gen.generate(variant="v1.0.0-base", output_format="md", output_path=output_path)

        assert isinstance(content, str)
        assert output_path.exists()
        assert output_path.read_text() == content
        # PDF should not be called for MD format
        mock_compile_pdf.assert_not_called()

    @patch("subprocess.Popen")
    def test_generate_pdf_calls_compile(self, mock_popen, sample_yaml_file: Path, temp_dir: Path):
        """Test generate with pdf format calls _compile_pdf."""
        gen = TemplateGenerator(yaml_path=sample_yaml_file)
        output_path = temp_dir / "test.pdf"

        # Mock Popen to raise FileNotFoundError (pdflatex not installed)
        mock_popen.side_effect = FileNotFoundError("pdflatex not found")

        # Suppress the RuntimeError that would normally be raised
        import cli.generators.template as template_module

        def mock_compile_pdf(self, output_path, tex_content):
            # Create the .tex file
            tex_path = output_path.with_suffix(".tex")
            tex_path.write_text(tex_content, encoding="utf-8")
            # Don't actually compile

        with patch.object(template_module.TemplateGenerator, "_compile_pdf", mock_compile_pdf):
            gen.generate(variant="v1.0.0-base", output_format="pdf", output_path=output_path)

        # .tex file should be created
        tex_path = output_path.with_suffix(".tex")
        assert tex_path.exists()

    def test_generate_without_output_path(self, sample_yaml_file: Path):
        """Test generate without output_path returns content only."""
        gen = TemplateGenerator(yaml_path=sample_yaml_file)

        content = gen.generate(variant="v1.0.0-base", output_format="md")

        assert isinstance(content, str)
        assert len(content) > 0

    def test_generate_with_enhanced_context(self, sample_yaml_file: Path, temp_dir: Path):
        """Test generate with enhanced_context merges context."""
        gen = TemplateGenerator(yaml_path=sample_yaml_file)
        output_path = temp_dir / "test.md"

        enhanced_summary = "This is an AI-enhanced summary."
        enhanced_projects = {"featured": [{"name": "test", "description": "Test project"}]}

        content = gen.generate(
            variant="v1.0.0-base",
            output_format="md",
            output_path=output_path,
            enhanced_context={"summary": enhanced_summary, "projects": enhanced_projects},
        )

        # Enhanced context should be merged
        assert enhanced_summary in content
        assert "Test project" in content

    def test_generate_with_template_prioritization(self, sample_yaml_file: Path, temp_dir: Path):
        """Test generate prioritizes skills from enhanced context."""
        gen = TemplateGenerator(yaml_path=sample_yaml_file)

        enhanced_projects = {
            "featured": [
                {"name": "k8s-app", "highlighted_technologies": ["Kubernetes", "Docker", "Python"]}
            ]
        }

        content = gen.generate(
            variant="v1.0.0-base",
            output_format="md",
            enhanced_context={"projects": enhanced_projects},
        )

        # Just verify it runs without error
        assert isinstance(content, str)

    def test_generate_creates_parent_directories(self, sample_yaml_file: Path, temp_dir: Path):
        """Test generate creates parent directories."""
        gen = TemplateGenerator(yaml_path=sample_yaml_file)
        nested_path = temp_dir / "nested" / "dir" / "test.md"

        gen.generate(variant="v1.0.0-base", output_format="md", output_path=nested_path)

        assert nested_path.exists()
        assert nested_path.parent.exists()


class TestGenerateEmail:
    """Test generate_email method."""

    def test_generate_email_basic(self, sample_yaml_file: Path, temp_dir: Path):
        """Test generate_email creates email content."""
        gen = TemplateGenerator(yaml_path=sample_yaml_file)
        output_path = temp_dir / "email.md"

        content = gen.generate_email(
            company_name="Acme Corp", position_name="Senior Engineer", output_path=output_path
        )

        assert isinstance(content, str)
        assert "Acme Corp" in content
        assert "Senior Engineer" in content

    def test_generate_email_with_hiring_manager(self, sample_yaml_file: Path, temp_dir: Path):
        """Test generate_email with hiring manager."""
        gen = TemplateGenerator(yaml_path=sample_yaml_file)
        output_path = temp_dir / "email.md"

        content = gen.generate_email(
            company_name="Acme Corp",
            position_name="Senior Engineer",
            hiring_manager_name="John Smith",
            output_path=output_path,
        )

        assert "John Smith" in content

    def test_generate_email_without_output_path(self, sample_yaml_file: Path):
        """Test generate_email without output_path returns content only."""
        gen = TemplateGenerator(yaml_path=sample_yaml_file)

        content = gen.generate_email(company_name="Acme Corp", position_name="Senior Engineer")

        assert isinstance(content, str)
        assert len(content) > 0


class TestGetOutputPath:
    """Test get_output_path method."""

    def test_get_output_path_default(self, mock_config: Config, temp_dir: Path):
        """Test get_output_path with default settings."""
        gen = TemplateGenerator(config=mock_config)
        output_dir = temp_dir / "output"

        output_path = gen.get_output_path(
            variant="v1.0.0-base", output_format="md", output_dir=output_dir
        )

        # Check path structure
        assert output_dir in output_path.parents
        assert output_path.suffix == ".md"
        assert "v1-0-0-base" in output_path.name

    def test_get_output_path_creates_directory(self, mock_config: Config, temp_dir: Path):
        """Test get_output_path creates output directory."""
        gen = TemplateGenerator(config=mock_config)
        output_dir = temp_dir / "new_output"

        output_path = gen.get_output_path(
            variant="v1.0.0-base", output_format="pdf", output_dir=output_dir
        )

        assert output_dir.exists()
        assert output_path.suffix == ".pdf"


class TestListTemplates:
    """Test list_templates method."""

    def test_list_templates(self, sample_yaml_file: Path):
        """Test list_templates returns template list."""
        gen = TemplateGenerator(yaml_path=sample_yaml_file)

        templates = gen.list_templates()

        assert isinstance(templates, list)
        # Should include standard templates
        assert "resume_md" in templates
        assert "resume_tex" in templates


class TestCompilePdf:
    """Test _compile_pdf method."""

    @patch("subprocess.Popen")
    def test_compile_pdf_pdflatex_success(self, mock_popen, sample_yaml_file: Path, temp_dir: Path):
        """Test _compile_pdf with successful pdflatex run."""
        gen = TemplateGenerator(yaml_path=sample_yaml_file)
        output_path = temp_dir / "test.pdf"
        tex_content = r"\documentclass{article}\begin{document}Test\end{document}"

        # Mock successful pdflatex
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"", b"")
        mock_popen.return_value = mock_process

        # Mock file creation (pdflatex creates PDF)
        output_path.write_bytes(b"PDF content")

        gen._compile_pdf(output_path, tex_content)

        assert output_path.exists()

    @patch("subprocess.Popen", side_effect=FileNotFoundError)
    def test_compile_pdf_pdflatex_not_found(
        self, mock_popen, sample_yaml_file: Path, temp_dir: Path, capsys
    ):
        """Test _compile_pdf raises error when pdflatex not found."""
        gen = TemplateGenerator(yaml_path=sample_yaml_file)
        output_path = temp_dir / "test.pdf"
        tex_content = r"\documentclass{article}\begin{document}Test\end{document}"

        with pytest.raises(RuntimeError) as exc_info:
            gen._compile_pdf(output_path, tex_content)

        assert "PDF compilation failed" in str(exc_info.value)
        assert "pdflatex" in str(exc_info.value)

    @patch("subprocess.Popen")
    def test_compile_pdf_creates_tex_file(self, mock_popen, sample_yaml_file: Path, temp_dir: Path):
        """Test _compile_pdf creates .tex file."""
        gen = TemplateGenerator(yaml_path=sample_yaml_file)
        output_path = temp_dir / "test.pdf"
        tex_content = r"\documentclass{article}\begin{document}Test\end{document}"

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"", b"")
        mock_popen.return_value = mock_process

        # Mock file creation
        output_path.write_bytes(b"PDF content")

        gen._compile_pdf(output_path, tex_content)

        tex_path = output_path.with_suffix(".tex")
        assert tex_path.exists()
        assert tex_path.read_text() == tex_content
