"""Unit tests for AIGenerator.tailor_data method."""

import json
import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from cli.generators.ai_generator import AIGenerator
from cli.utils.config import Config


def _make_anthropic_response(text: str):
    """Helper to build a fake Anthropic-style response object."""
    return SimpleNamespace(content=[SimpleNamespace(text=text)])


def _make_openai_response(text: str):
    """Helper to build a fake OpenAI-style response object."""
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


@pytest.fixture
def base_resume_data():
    """Base resume data for testing."""
    return {
        "meta": {"version": "1.0"},
        "contact": {"name": "Alice Candidate", "email": "alice@example.com"},
        "professional_summary": {"base": "Experienced engineer"},
        "experience": [
            {
                "company": "Acme",
                "title": "Engineer",
                "start_date": "2020-01",
                "bullets": [{"text": "Did work"}],
            }
        ],
    }


@pytest.fixture
def job_description():
    """Job description for testing."""
    return "Senior Software Engineer working with distributed systems."


def _build_generator(provider: str, monkeypatch) -> AIGenerator:
    """Build an AIGenerator with mocked client for testing."""
    # Set required environment variables
    monkeypatch.setenv("AI_PROVIDER", provider)
    if provider == "anthropic":
        monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy-key")
    elif provider == "openai":
        monkeypatch.setenv("OPENAI_API_KEY", "dummy-key")

    # Create generator - will initialize real client but we'll replace it
    with patch.object(Config, "ai_provider", provider):
        config = Config()
        config.set("ai.provider", provider)
        generator = AIGenerator(yaml_path=None, config=config)

    return generator


def test_tailor_data_anthropic_markdown_json_extraction(
    base_resume_data, job_description, monkeypatch
):
    """
    Anthropic branch: response is markdown text with JSON inside a fenced code block.
    tailor_data should extract and parse the JSON.
    """
    generator = _build_generator("anthropic", monkeypatch)

    tailored_payload = {
        "meta": {"version": "1.0"},
        "contact": {"name": "Alice Candidate", "email": "alice@example.com"},
        "professional_summary": {"base": "Tailored summary for the job"},
        "experience": [
            {
                "company": "Acme",
                "title": "Senior Engineer",
                "start_date": "2020-01",
                "bullets": [{"text": "Did senior work"}],
            }
        ],
    }

    markdown_response = """
    Here is your tailored resume data:

    ```json
    {
      "meta": {"version": "1.0"},
      "contact": {"name": "Alice Candidate", "email": "alice@example.com"},
      "professional_summary": {"base": "Tailored summary for the job"},
      "experience": [
        {
          "company": "Acme",
          "title": "Senior Engineer",
          "start_date": "2020-01",
          "bullets": [{"text": "Did senior work"}]
        }
      ]
    }
    ```

    Let me know if you need further changes.
    """

    # Mock the Anthropic client
    fake_client = SimpleNamespace(
        messages=SimpleNamespace(
            create=MagicMock(return_value=_make_anthropic_response(markdown_response))
        )
    )
    monkeypatch.setattr(generator, "client", fake_client, raising=False)

    result = generator.tailor_data(base_resume_data, job_description)

    assert result == tailored_payload


def test_tailor_data_anthropic_plain_json(base_resume_data, job_description, monkeypatch):
    """
    Anthropic branch: response is plain JSON (no markdown wrappers).
    tailor_data should parse it directly.
    """
    generator = _build_generator("anthropic", monkeypatch)

    tailored_payload = {
        "meta": {"version": "1.0"},
        "contact": {"name": "Alice Candidate", "email": "alice@example.com"},
        "professional_summary": {"base": "Anthropic tailored summary"},
        "experience": [
            {
                "company": "Acme",
                "title": "Staff Engineer",
                "start_date": "2020-01",
                "bullets": [{"text": "Did staff work"}],
            }
        ],
    }

    plain_json_response = json.dumps(tailored_payload)

    fake_client = SimpleNamespace(
        messages=SimpleNamespace(
            create=MagicMock(return_value=_make_anthropic_response(plain_json_response))
        )
    )
    monkeypatch.setattr(generator, "client", fake_client, raising=False)

    result = generator.tailor_data(base_resume_data, job_description)

    assert result == tailored_payload


def test_tailor_data_openai_markdown_json(base_resume_data, job_description, monkeypatch):
    """
    OpenAI branch: response is markdown text with JSON inside a fenced code block.
    tailor_data should extract and parse the JSON.
    """
    generator = _build_generator("openai", monkeypatch)

    tailored_payload = {
        "meta": {"version": "1.0"},
        "contact": {"name": "Alice Candidate", "email": "alice@example.com"},
        "professional_summary": {"base": "OpenAI tailored summary"},
        "experience": [
            {
                "company": "Acme",
                "title": "Senior Engineer",
                "start_date": "2020-01",
                "bullets": [{"text": "Did senior work"}],
            }
        ],
    }

    markdown_response = """
    ```json
    {
      "meta": {"version": "1.0"},
      "contact": {"name": "Alice Candidate", "email": "alice@example.com"},
      "professional_summary": {"base": "OpenAI tailored summary"},
      "experience": [
        {
          "company": "Acme",
          "title": "Senior Engineer",
          "start_date": "2020-01",
          "bullets": [{"text": "Did senior work"}]
        }
      ]
    }
    ```
    """

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=MagicMock(return_value=_make_openai_response(markdown_response))
            )
        )
    )
    monkeypatch.setattr(generator, "client", fake_client, raising=False)

    result = generator.tailor_data(base_resume_data, job_description)

    assert result == tailored_payload


def test_tailor_data_openai_plain_json(base_resume_data, job_description, monkeypatch):
    """
    OpenAI branch: response is a plain JSON string; tailor_data should parse it directly.
    """
    generator = _build_generator("openai", monkeypatch)

    tailored_payload = {
        "meta": {"version": "1.0"},
        "contact": {"name": "Alice Candidate", "email": "alice@example.com"},
        "professional_summary": {"base": "OpenAI plain tailored summary"},
        "experience": [
            {
                "company": "Acme",
                "title": "Staff Engineer",
                "start_date": "2020-01",
                "bullets": [{"text": "Did staff work"}],
            }
        ],
    }

    plain_json_response = json.dumps(tailored_payload)

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=MagicMock(return_value=_make_openai_response(plain_json_response))
            )
        )
    )
    monkeypatch.setattr(generator, "client", fake_client, raising=False)

    result = generator.tailor_data(base_resume_data, job_description)

    assert result == tailored_payload


@pytest.mark.parametrize("provider", ["anthropic", "openai"])
def test_tailor_data_invalid_json_falls_back_to_original(
    base_resume_data, job_description, monkeypatch, capsys, provider
):
    """
    For invalid/partial JSON or other parsing errors, tailor_data should print a warning
    and return the original resume_data unchanged.
    """
    generator = _build_generator(provider, monkeypatch)

    invalid_json_response = "{ this is not valid JSON "

    if provider == "anthropic":
        fake_client = SimpleNamespace(
            messages=SimpleNamespace(
                create=MagicMock(return_value=_make_anthropic_response(invalid_json_response))
            )
        )
    else:
        fake_client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=MagicMock(return_value=_make_openai_response(invalid_json_response))
                )
            )
        )

    monkeypatch.setattr(generator, "client", fake_client, raising=False)

    result = generator.tailor_data(base_resume_data, job_description)

    # tailor_data should fall back to the original resume_data
    assert result == base_resume_data

    # Should print a warning about the failure (captured via capsys)
    captured = capsys.readouterr()
    assert "warning" in captured.out.lower() or "warning" in captured.err.lower()


def test_tailor_data_non_greedy_json_extraction(base_resume_data, job_description, monkeypatch):
    """
    Test that the non-greedy regex correctly extracts JSON when there are multiple
    JSON-like structures in the response.
    """
    generator = _build_generator("anthropic", monkeypatch)

    tailored_payload = {
        "meta": {"version": "1.0"},
        "contact": {"name": "Alice Candidate", "email": "alice@example.com"},
        "professional_summary": {"base": "Correctly extracted"},
        "experience": [],
    }

    # Response with multiple braces - non-greedy should extract the first complete JSON
    response_with_extra = """
    Here's some data: {"extra": "stuff", "nested": {"more": "data"}}

    And here's the actual resume:
    ```json
    {
      "meta": {"version": "1.0"},
      "contact": {"name": "Alice Candidate", "email": "alice@example.com"},
      "professional_summary": {"base": "Correctly extracted"},
      "experience": []
    }
    ```
    """

    fake_client = SimpleNamespace(
        messages=SimpleNamespace(
            create=MagicMock(return_value=_make_anthropic_response(response_with_extra))
        )
    )
    monkeypatch.setattr(generator, "client", fake_client, raising=False)

    result = generator.tailor_data(base_resume_data, job_description)

    # Should extract the fenced JSON, not the first { encountered
    assert result == tailored_payload
