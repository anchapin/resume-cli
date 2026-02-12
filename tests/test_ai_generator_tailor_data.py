import json
import os
import sys
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

# Mock anthropic and openai modules if not installed
# This is necessary because the environment seems to have issues importing them
# even after installation, or they are missing.
if "anthropic" not in sys.modules:
    sys.modules["anthropic"] = MagicMock()
if "openai" not in sys.modules:
    sys.modules["openai"] = MagicMock()

from cli.generators.ai_generator import AIGenerator

def _make_anthropic_response(text: str):
    """Helper to build a fake Anthropic-style response object."""
    # Anthropic response: message.content[0].text
    # We mock message
    return SimpleNamespace(
        content=[SimpleNamespace(text=text)]
    )

def _make_openai_response(text: str):
    """Helper to build a fake OpenAI-style response object."""
    # OpenAI response: response.choices[0].message.content
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=text)
            )
        ]
    )

@pytest.fixture
def base_resume_data():
    return {
        "name": "Alice Candidate",
        "summary": "Experienced engineer",
        "experience": [{"company": "Acme", "title": "Engineer"}],
    }

@pytest.fixture
def job_description():
    return "Senior Software Engineer working with distributed systems."

def _build_generator(provider: str) -> AIGenerator:
    # AIGenerator uses config to determine provider, not env var (except for API keys)
    # We need to mock Config object or set up config dict
    with patch.dict(
        os.environ,
        {
            "ANTHROPIC_API_KEY": "dummy",
            "OPENAI_API_KEY": "dummy",
        },
        clear=False,
    ):
        with patch("cli.generators.ai_generator.Config") as MockConfig:
            mock_config = MockConfig.return_value
            mock_config.ai_provider = provider
            mock_config.get.return_value = "claude-3-opus" # or gpt-4
            mock_config.anthropic_base_url = None
            mock_config.openai_base_url = None

            # Need to also patch import availability
            with patch("cli.generators.ai_generator.ANTHROPIC_AVAILABLE", True), \
                 patch("cli.generators.ai_generator.OPENAI_AVAILABLE", True), \
                 patch("anthropic.Anthropic"), \
                 patch("openai.OpenAI"):
                return AIGenerator(config=mock_config)

def test_tailor_data_anthropic_markdown_json_extraction(base_resume_data, job_description, monkeypatch):
    """
    Anthropic branch: response is markdown text with JSON inside a fenced code block.
    tailor_data should extract and parse the JSON.
    """
    generator = _build_generator("anthropic")

    tailored_payload = {
        "name": "Alice Candidate",
        "summary": "Tailored summary for the job",
        "experience": [{"company": "Acme", "title": "Senior Engineer"}],
    }

    markdown_response = """
    Here is your tailored resume data:

    ```json
    {
      "name": "Alice Candidate",
      "summary": "Tailored summary for the job",
      "experience": [
        {"company": "Acme", "title": "Senior Engineer"}
      ]
    }
    ```

    Let me know if you need further changes.
    """

    # Mock client.messages.create
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _make_anthropic_response(markdown_response)
    monkeypatch.setattr(generator, "client", fake_client, raising=False)

    result = generator.tailor_data(base_resume_data, job_description)

    assert result == tailored_payload

def test_tailor_data_openai_plain_json(base_resume_data, job_description, monkeypatch):
    """
    OpenAI branch: response is a plain JSON string; tailor_data should parse it directly.
    """
    generator = _build_generator("openai")

    tailored_payload = {
        "name": "Alice Candidate",
        "summary": "OpenAI tailored summary",
        "experience": [{"company": "Acme", "title": "Staff Engineer"}],
    }

    plain_json_response = json.dumps(tailored_payload)

    # Mock client.chat.completions.create
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = _make_openai_response(plain_json_response)
    monkeypatch.setattr(generator, "client", fake_client, raising=False)

    result = generator.tailor_data(base_resume_data, job_description)

    assert result == tailored_payload

@pytest.mark.parametrize("provider", ["anthropic", "openai"])
def test_tailor_data_invalid_json_raises_exception(base_resume_data, job_description, monkeypatch, caplog, provider):
    """
    For invalid/partial JSON or other parsing errors, tailor_data should log a warning
    and raise RuntimeError (changed behavior).
    """
    generator = _build_generator(provider)

    invalid_json_response = "{ this is not valid JSON "

    fake_client = MagicMock()
    if provider == "anthropic":
        fake_client.messages.create.return_value = _make_anthropic_response(invalid_json_response)
    else:
        fake_client.chat.completions.create.return_value = _make_openai_response(invalid_json_response)

    monkeypatch.setattr(generator, "client", fake_client, raising=False)

    # Verify exception is raised
    with pytest.raises(RuntimeError, match="Failed to parse AI response"):
        generator.tailor_data(base_resume_data, job_description)
