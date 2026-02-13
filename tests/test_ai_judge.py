"""Unit tests for AIJudge class."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from cli.generators.ai_judge import AIJudge, create_ai_judge
from cli.utils.config import Config


def _make_anthropic_response(text: str):
    """Helper to build fake Anthropic response."""
    return SimpleNamespace(content=[SimpleNamespace(text=text)])


def _make_openai_response(text: str):
    """Helper to build fake OpenAI response."""
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


class TestAIJudgeInitialization:
    """Test AIJudge initialization."""

    def test_init_with_client(self):
        """Test initialization with client and provider."""
        config = Config()
        mock_client = MagicMock()

        judge = AIJudge(mock_client, "anthropic", config)

        assert judge.client == mock_client
        assert judge.provider == "anthropic"
        assert judge.config == config


class TestJudgeCoverLetter:
    """Test judge_cover_letter method."""

    def test_judge_cover_letter_single_version(self, sample_yaml_file: Path):
        """Test judge returns single version when only one provided."""
        config = Config()
        mock_client = MagicMock()
        judge = AIJudge(mock_client, "anthropic", config)

        versions = [{"opening_hook": "Test"}]
        job_desc = "Job description"
        job_details = {"company": "Acme", "position": "Engineer"}
        resume_context = "Resume summary"

        selected, justification = judge.judge_cover_letter(
            versions, job_desc, job_details, resume_context
        )

        assert selected == versions[0]
        assert "Only one version" in justification

    def test_judge_cover_letter_multiple_versions(self, sample_yaml_file: Path, monkeypatch):
        """Test judge selects best from multiple versions."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        config = Config()
        mock_client = SimpleNamespace(
            messages=SimpleNamespace(
                create=MagicMock(
                    return_value=_make_anthropic_response(
                        '{"selected": 1, "action": "select", "justification": "Version 2 is best"}'
                    )
                )
            )
        )

        judge = AIJudge(mock_client, "anthropic", config)

        versions = [
            {"opening_hook": "Version 1"},
            {"opening_hook": "Version 2"},
            {"opening_hook": "Version 3"},
        ]
        job_desc = "Job description"
        job_details = {"company": "Acme"}
        resume_context = "Resume summary"

        selected, justification = judge.judge_cover_letter(
            versions, job_desc, job_details, resume_context
        )

        assert selected == versions[1]  # Selected version 2
        assert "Version 2 is best" in justification

    def test_judge_cover_letter_combine_action(self, sample_yaml_file: Path, monkeypatch):
        """Test judge combines elements from multiple versions."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        config = Config()
        mock_client = SimpleNamespace(
            messages=SimpleNamespace(
                create=MagicMock(
                    return_value=_make_anthropic_response(
                        '{"selected": 0, "action": "combine", "justification": "Combining best elements", "selection": {"opening_hook": 1, "professional_summary": 2}}'
                    )
                )
            )
        )

        judge = AIJudge(mock_client, "anthropic", config)

        versions = [
            {"opening_hook": "V1", "professional_summary": "S1"},
            {"opening_hook": "V2", "professional_summary": "S2"},
            {"opening_hook": "V3", "professional_summary": "S3"},
        ]
        job_desc = "Job description"
        job_details = {"company": "Acme"}
        resume_context = "Resume summary"

        selected, justification = judge.judge_cover_letter(
            versions, job_desc, job_details, resume_context
        )

        assert selected["opening_hook"] == "V1"  # From version 1
        assert selected["professional_summary"] == "S2"  # From version 2
        assert "Combining best elements" in justification

    def test_judge_cover_letter_error_fallback(self, sample_yaml_file: Path, monkeypatch):
        """Test judge falls back to first version on error."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        config = Config()
        mock_client = SimpleNamespace(
            messages=SimpleNamespace(create=MagicMock(side_effect=Exception("API error")))
        )

        judge = AIJudge(mock_client, "anthropic", config)

        versions = [{"opening_hook": "V1"}, {"opening_hook": "V2"}, {"opening_hook": "V3"}]
        job_desc = "Job description"
        job_details = {"company": "Acme"}
        resume_context = "Resume summary"

        selected, justification = judge.judge_cover_letter(
            versions, job_desc, job_details, resume_context
        )

        assert selected == versions[0]
        assert "failed" in justification.lower()


class TestJudgeResumeCustomization:
    """Test judge_resume_customization method."""

    def test_judge_resume_customization_single_version(self, sample_yaml_file: Path):
        """Test judge returns single version when only one provided."""
        config = Config()
        mock_client = MagicMock()
        judge = AIJudge(mock_client, "anthropic", config)

        versions = [{"keywords": ["Python"]}]
        job_desc = "Job description"
        resume_context = "Resume summary"

        selected, justification = judge.judge_resume_customization(
            versions, job_desc, resume_context
        )

        assert selected == versions[0]
        assert "Only one version" in justification

    def test_judge_resume_customization_multiple_versions(
        self, sample_yaml_file: Path, monkeypatch
    ):
        """Test judge selects best from multiple versions."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        config = Config()
        mock_client = SimpleNamespace(
            messages=SimpleNamespace(
                create=MagicMock(
                    return_value=_make_anthropic_response(
                        '{"selected": 2, "action": "select", "justification": "Version 3 has best keyword match"}'
                    )
                )
            )
        )

        judge = AIJudge(mock_client, "anthropic", config)

        versions = [{"keywords": ["Python"]}, {"keywords": ["Java"]}, {"keywords": ["Go"]}]
        job_desc = "Job description"
        resume_context = "Resume summary"

        selected, justification = judge.judge_resume_customization(
            versions, job_desc, resume_context
        )

        assert selected == versions[2]
        assert "Version 3 has best keyword match" in justification


class TestJudgeResumeText:
    """Test judge_resume_text method."""

    def test_judge_resume_text_single_version(self, sample_yaml_file: Path):
        """Test judge returns single version when only one provided."""
        config = Config()
        mock_client = MagicMock()
        judge = AIJudge(mock_client, "anthropic", config)

        versions = ["Resume version 1"]
        job_desc = "Job description"
        base_resume = "Original resume"

        selected, justification = judge.judge_resume_text(versions, job_desc, base_resume)

        assert selected == versions[0]
        assert "Only one version" in justification

    def test_judge_resume_text_multiple_versions(self, sample_yaml_file: Path, monkeypatch):
        """Test judge selects best from multiple versions."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        config = Config()
        mock_client = SimpleNamespace(
            messages=SimpleNamespace(
                create=MagicMock(
                    return_value=_make_anthropic_response(
                        '{"selected": 0, "justification": "First version is best"}'
                    )
                )
            )
        )

        judge = AIJudge(mock_client, "anthropic", config)

        versions = ["Resume version 1", "Resume version 2", "Resume version 3"]
        job_desc = "Job description"
        base_resume = "Original resume"

        selected, justification = judge.judge_resume_text(versions, job_desc, base_resume)

        assert selected == versions[0]
        assert "First version is best" in justification


class TestParseJudgeResponse:
    """Test _parse_judge_response method."""

    def test_parse_judge_response_valid_json(self):
        """Test parsing valid JSON response."""
        config = Config()
        mock_client = MagicMock()
        judge = AIJudge(mock_client, "anthropic", config)

        response = '{"selected": 1, "action": "select", "justification": "Best"}'
        parsed = judge._parse_judge_response(response)

        assert parsed["selected"] == 1
        assert parsed["action"] == "select"
        assert parsed["justification"] == "Best"

    def test_parse_judge_response_json_in_text(self):
        """Test parsing JSON within larger text response."""
        config = Config()
        mock_client = MagicMock()
        judge = AIJudge(mock_client, "anthropic", config)

        response = 'Here is my analysis:\n{"selected": 2, "action": "select", "justification": "Great"}\n\nHope this helps!'
        parsed = judge._parse_judge_response(response)

        assert parsed["selected"] == 2
        assert parsed["action"] == "select"

    def test_parse_judge_response_invalid_json(self):
        """Test parsing invalid JSON returns default."""
        config = Config()
        mock_client = MagicMock()
        judge = AIJudge(mock_client, "anthropic", config)

        response = "This is not JSON at all"
        parsed = judge._parse_judge_response(response)

        assert parsed["selected"] == 0
        assert parsed["action"] == "select"
        assert "Failed to parse" in parsed["justification"]


class TestCombineVersions:
    """Test _combine_versions method."""

    def test_combine_versions(self):
        """Test combining elements from multiple versions."""
        config = Config()
        mock_client = MagicMock()
        judge = AIJudge(mock_client, "anthropic", config)

        versions = [
            {"opening_hook": "V1", "professional_summary": "S1", "achievements": "A1"},
            {"opening_hook": "V2", "professional_summary": "S2", "achievements": "A2"},
            {"opening_hook": "V3", "professional_summary": "S3", "achievements": "A3"},
        ]

        selection = {"opening_hook": 1, "professional_summary": 2, "achievements": 3}

        combined = judge._combine_versions(versions, selection)

        assert combined["opening_hook"] == "V1"
        assert combined["professional_summary"] == "S2"
        assert combined["achievements"] == "A3"

    def test_combine_versions_invalid_index(self):
        """Test combining with invalid index."""
        config = Config()
        mock_client = MagicMock()
        judge = AIJudge(mock_client, "anthropic", config)

        versions = [{"key1": "V1"}, {"key1": "V2"}]

        selection = {"key1": 5}  # Index 5 doesn't exist

        combined = judge._combine_versions(versions, selection)

        # Should not include the key (index out of range)
        assert "key1" not in combined


class TestCreateAIJudgeFactory:
    """Test create_ai_judge factory function."""

    def test_create_ai_judge(self):
        """Test factory function creates AIJudge instance."""
        config = Config()
        mock_client = MagicMock()

        judge = create_ai_judge(mock_client, "anthropic", config)

        assert isinstance(judge, AIJudge)
        assert judge.client == mock_client
        assert judge.provider == "anthropic"
        assert judge.config == config
