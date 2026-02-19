import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from cli.generators.cover_letter_generator import CoverLetterGenerator
from cli.utils.config import Config


@pytest.fixture
def mock_config():
    config = MagicMock(spec=Config)
    config.ai_provider = "openai"  # or anthropic
    config.get.return_value = "dummy"
    return config


@pytest.fixture
def generator(mock_config, tmp_path):
    # Mock resume.yaml
    resume_path = tmp_path / "resume.yaml"
    with open(resume_path, "w") as f:
        f.write(
            "contact:\n  name: Test User\n  email: test@example.com\n  urls:\n    linkedin: https://linkedin.com/in/test\n    github: https://github.com/test\n"
        )

    # Mock API keys to allow initialization
    with patch.dict(os.environ, {"OPENAI_API_KEY": "dummy", "ANTHROPIC_API_KEY": "dummy"}):
        gen = CoverLetterGenerator(yaml_path=resume_path, config=mock_config)
        yield gen


def test_latex_injection_prevention(generator):
    """Test that LaTeX special characters in user input are escaped."""

    # Malicious input
    malicious_input = "\\input{/etc/passwd}"
    malicious_company = f"BadCorp {malicious_input}"

    # Content dict
    content = {
        "opening_hook": "Hello",
        "professional_summary": "Summary",
        "key_achievements": [],
        "skills_highlight": [],
        "company_alignment": None,
        "connection": None,
    }

    job_details = {"company": malicious_company, "position": "Hacker"}

    # Render
    output = generator._render_latex(content, job_details)

    # Check for escaped input
    # Expected: \textbackslash{}input\{/etc/passwd\}
    escaped_input = "\\textbackslash{}input\\{/etc/passwd\\}"

    assert malicious_input not in output, "Unescaped malicious input found!"
    assert (
        escaped_input in output or "\\textbackslash{}input{" in output
    ), "Input was not correctly escaped!"

    # Check specifically in metadata (common injection point)
    assert f"pdftitle={{ Test User - Cover Letter - {malicious_company} }}" not in output
