from unittest.mock import patch

from markupsafe import Markup

from cli.generators.template import TemplateGenerator
from cli.utils.template_filters import latex_escape


def test_latex_escape_security():
    """Test that latex_escape properly escapes malicious input."""
    # Basic escaping
    assert latex_escape("Alice & Bob") == Markup(r"Alice \& Bob")

    # Backslash escaping (injection prevention)
    assert latex_escape(r"\input{/etc/passwd}") == Markup(r"\textbackslash{}input\{/etc/passwd\}")

    # Braces escaping
    assert latex_escape("{}") == Markup(r"\{\}")

    # Markdown bold to LaTeX
    assert latex_escape("**bold**") == Markup(r"\textbf{bold}")

    # Markdown bold with special chars
    assert latex_escape("**bold & safe**") == Markup(r"\textbf{bold \& safe}")

    # Idempotency
    escaped = latex_escape("foo & bar")
    assert latex_escape(escaped) == escaped
    assert isinstance(escaped, Markup)


def test_template_generator_autoescape():
    """Test that TemplateGenerator automatically escapes variables in LaTeX templates."""
    # Mock ResumeYAML and Config
    with patch("cli.generators.template.ResumeYAML") as MockResumeYAML, patch(
        "cli.generators.template.Config"
    ):

        mock_yaml = MockResumeYAML.return_value
        mock_yaml.get_contact.return_value = {"name": "Alice & Bob"}
        # Mock other methods to return empty/defaults
        mock_yaml.get_variant.return_value = {}
        mock_yaml.get_summary.return_value = ""
        mock_yaml.get_skills.return_value = {}
        mock_yaml.get_experience.return_value = []
        mock_yaml.get_education.return_value = []
        mock_yaml.get_projects.return_value = {}
        mock_yaml.data = {}

        generator = TemplateGenerator()

        # Test tex_env directly
        template = generator.tex_env.from_string("{{ contact.name }}")
        rendered = template.render(contact={"name": "Alice & Bob"})

        assert rendered == r"Alice \& Bob"

        # Test double escaping prevention (if variable is already marked safe)
        safe_var = Markup(r"Already \& Safe")
        template = generator.tex_env.from_string("{{ var }}")
        rendered = template.render(var=safe_var)
        assert rendered == r"Already \& Safe"


def test_custom_template_loading():
    """Test that custom templates are loaded with the correct environment."""
    with patch("cli.generators.template.ResumeYAML"), patch(
        "cli.generators.template.Config"
    ), patch("pathlib.Path.exists", return_value=True), patch(
        "pathlib.Path.read_text", return_value="{{ '&'|latex_escape }}"
    ):

        generator = TemplateGenerator()
        generator.yaml_handler.get_contact.return_value = {"name": "Test"}
        # Mock other required methods
        generator.yaml_handler.get_variant.return_value = {}
        generator.yaml_handler.get_summary.return_value = ""
        generator.yaml_handler.get_skills.return_value = {}
        generator.yaml_handler.get_experience.return_value = []
        generator.yaml_handler.get_education.return_value = []
        generator.yaml_handler.get_projects.return_value = {}
        generator.yaml_handler.data = {}

        # Generate LaTeX
        content = generator.generate(
            variant="base", output_format="tex", custom_template_path="dummy.j2"
        )

        # Should be escaped
        assert content == r"\&"
