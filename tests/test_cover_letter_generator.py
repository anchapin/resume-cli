"""Unit tests for CoverLetterGenerator class."""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from cli.generators.cover_letter_generator import CoverLetterGenerator, generate_cover_letter
from cli.utils.config import Config


def _make_anthropic_response(text: str):
    """Helper to build fake Anthropic response."""
    return SimpleNamespace(content=[SimpleNamespace(text=text)])


def _make_openai_response(text: str):
    """Helper to build fake OpenAI response."""
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


class TestCoverLetterGeneratorInitialization:
    """Test CoverLetterGenerator initialization."""

    def test_init_anthropic_requires_api_key(self, sample_yaml_file: Path, monkeypatch):
        """Test initialization raises error without Anthropic API key."""
        monkeypatch.setenv("AI_PROVIDER", "anthropic")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(ValueError) as exc_info:
            CoverLetterGenerator(yaml_path=sample_yaml_file)

        assert "ANTHROPIC_API_KEY" in str(exc_info.value)

    def test_init_openai_requires_api_key(self, sample_yaml_file: Path, monkeypatch):
        """Test initialization raises error without OpenAI API key."""
        monkeypatch.setenv("AI_PROVIDER", "openai")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(ValueError) as exc_info:
            CoverLetterGenerator(yaml_path=sample_yaml_file)

        assert "OPENAI_API_KEY" in str(exc_info.value)

    def test_init_anthropic_with_api_key(self, sample_yaml_file: Path, monkeypatch):
        """Test initialization with Anthropic API key."""
        monkeypatch.setenv("AI_PROVIDER", "anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        gen = CoverLetterGenerator(yaml_path=sample_yaml_file)
        assert gen.provider == "anthropic"

    def test_init_openai_with_api_key(self, sample_yaml_file: Path, monkeypatch):
        """Test initialization with OpenAI API key."""
        monkeypatch.setenv("AI_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        gen = CoverLetterGenerator(yaml_path=sample_yaml_file)
        assert gen.provider == "openai"


class TestExtractJobDetails:
    """Test _extract_job_details method."""

    def test_extract_job_details_with_company(self, sample_yaml_file: Path, monkeypatch):
        """Test extraction with company name provided."""
        monkeypatch.setenv("AI_PROVIDER", "anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        gen = CoverLetterGenerator(yaml_path=sample_yaml_file)
        gen.client = SimpleNamespace(
            messages=SimpleNamespace(
                create=MagicMock(
                    return_value=_make_anthropic_response(
                        '{"position": "Engineer", "requirements": ["Python"], "company_mission": null}'
                    )
                )
            )
        )

        job_desc = "We are looking for a Python Engineer"
        details = gen._extract_job_details(job_desc, "Acme Corp")

        assert details["company"] == "Acme Corp"
        assert "Engineer" in details.get("position", "")

    def test_extract_job_details_without_company(self, sample_yaml_file: Path, monkeypatch):
        """Test extraction without company name."""
        monkeypatch.setenv("AI_PROVIDER", "anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        gen = CoverLetterGenerator(yaml_path=sample_yaml_file)
        gen.client = SimpleNamespace(
            messages=SimpleNamespace(
                create=MagicMock(
                    return_value=_make_anthropic_response(
                        '{"position": "Engineer", "requirements": ["Python"], "company": "TestCompany"}'
                    )
                )
            )
        )

        job_desc = "We are looking for a Python Engineer at TestCompany"
        details = gen._extract_job_details(job_desc)

        assert "Engineer" in details.get("position", "")


class TestDetermineQuestions:
    """Test _determine_questions method."""

    def test_determine_questions_includes_motivation(self, sample_yaml_file: Path):
        """Test questions always include motivation."""
        gen = CoverLetterGenerator(yaml_path=sample_yaml_file)

        job_details = {"company": "Acme", "position": "Engineer"}

        questions = gen._determine_questions(job_details)

        assert len(questions) >= 1
        assert any(q["key"] == "motivation" for q in questions)
        assert questions[0]["required"] is True

    def test_determine_questions_includes_company_alignment(self, sample_yaml_file: Path):
        """Test questions include company_alignment when mission present."""
        gen = CoverLetterGenerator(yaml_path=sample_yaml_file)

        job_details = {
            "company": "Acme",
            "position": "Engineer",
            "company_mission": "Build great software",
        }

        questions = gen._determine_questions(job_details)

        alignment_questions = [q for q in questions if q["key"] == "company_alignment"]
        assert len(alignment_questions) == 1
        assert alignment_questions[0]["required"] is False

    def test_determine_questions_includes_connection(self, sample_yaml_file: Path):
        """Test questions always include connection."""
        gen = CoverLetterGenerator(yaml_path=sample_yaml_file)

        job_details = {"company": "Acme", "position": "Engineer"}

        questions = gen._determine_questions(job_details)

        connection_questions = [q for q in questions if q["key"] == "connection"]
        assert len(connection_questions) == 1


class TestGetFallbackContent:
    """Test _get_fallback_content method."""

    def test_get_fallback_content_returns_dict(self, sample_yaml_file: Path):
        """Test fallback content returns proper structure."""
        gen = CoverLetterGenerator(yaml_path=sample_yaml_file)

        job_details = {"company": "Acme", "position": "Engineer"}

        summary = "Experienced engineer with 10 years"
        fallback = gen._get_fallback_content(job_details, summary)

        assert isinstance(fallback, dict)
        assert "opening_hook" in fallback
        assert "professional_summary" in fallback
        assert "key_achievements" in fallback
        assert "skills_highlight" in fallback

    def test_get_fallback_content_includes_summary(self, sample_yaml_file: Path):
        """Test fallback content includes summary."""
        gen = CoverLetterGenerator(yaml_path=sample_yaml_file)

        job_details = {"company": "Acme"}
        summary = "This is my summary"
        fallback = gen._get_fallback_content(job_details, summary)

        assert summary in fallback["professional_summary"]


class TestGenerateSmartGuesses:
    """Test _generate_smart_guesses method."""

    def test_generate_smart_guesses_returns_dict(self, sample_yaml_file: Path, monkeypatch):
        """Test smart guesses returns dict with required keys."""
        monkeypatch.setenv("AI_PROVIDER", "anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        gen = CoverLetterGenerator(yaml_path=sample_yaml_file)
        gen.client = SimpleNamespace(
            messages=SimpleNamespace(
                create=MagicMock(
                    return_value=_make_anthropic_response(
                        '{"motivation": "Interested", "company_alignment": null, "connection": null}'
                    )
                )
            )
        )

        job_desc = "Looking for engineer"
        job_details = {"company": "Acme", "position": "Engineer"}

        guesses = gen._generate_smart_guesses(job_desc, job_details, "base")

        assert isinstance(guesses, dict)
        assert "motivation" in guesses
        assert "company_alignment" in guesses
        assert "connection" in guesses


class TestBuildCoverLetterPrompt:
    """Test _build_cover_letter_prompt method."""

    def test_build_prompt_includes_job_details(self, sample_yaml_file: Path):
        """Test prompt includes job details."""
        gen = CoverLetterGenerator(yaml_path=sample_yaml_file)

        job_desc = "Looking for Python engineer"
        job_details = {"company": "Acme", "position": "Senior Engineer"}
        resume_context = "Resume context"
        qa = {"motivation": "Excited about role"}

        prompt = gen._build_cover_letter_prompt(job_desc, job_details, resume_context, qa)

        assert "Acme" in prompt
        assert "Senior Engineer" in prompt
        assert job_desc in prompt
        assert "Excited about role" in prompt


class TestGenerateSingleVersion:
    """Test _generate_single_version method."""

    def test_generate_single_version_anthropic(self, sample_yaml_file: Path, monkeypatch):
        """Test single version generation with Anthropic."""
        monkeypatch.setenv("AI_PROVIDER", "anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        gen = CoverLetterGenerator(yaml_path=sample_yaml_file)
        gen.client = SimpleNamespace(
            messages=SimpleNamespace(
                create=MagicMock(
                    return_value=_make_anthropic_response(
                        '{"opening_hook": "Dear hiring manager", "professional_summary": "Summary"}'
                    )
                )
            )
        )

        prompt = "Generate cover letter"
        result = gen._generate_single_version(prompt)

        assert result is not None
        assert "opening_hook" in result
        assert "professional_summary" in result

    def test_generate_single_version_openai(self, sample_yaml_file: Path, monkeypatch):
        """Test single version generation with OpenAI."""
        monkeypatch.setenv("AI_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        gen = CoverLetterGenerator(yaml_path=sample_yaml_file)
        gen.client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=MagicMock(
                        return_value=_make_openai_response(
                            '{"opening_hook": "Hello", "professional_summary": "My summary"}'
                        )
                    )
                )
            )
        )

        prompt = "Generate cover letter"
        result = gen._generate_single_version(prompt)

        assert result is not None
        assert "opening_hook" in result

    def test_generate_single_version_invalid_json(self, sample_yaml_file: Path, monkeypatch):
        """Test single version returns None on invalid JSON."""
        monkeypatch.setenv("AI_PROVIDER", "anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        gen = CoverLetterGenerator(yaml_path=sample_yaml_file)
        gen.client = SimpleNamespace(
            messages=SimpleNamespace(
                create=MagicMock(return_value=_make_anthropic_response("not valid json"))
            )
        )

        result = gen._generate_single_version("Generate")

        assert result is None


class TestGenerateInteractive:
    """Test generate_interactive method."""

    def test_generate_interactive(self, sample_yaml_file: Path, monkeypatch, mocker):
        """Test interactive generation with mocked input."""
        monkeypatch.setenv("AI_PROVIDER", "anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        gen = CoverLetterGenerator(yaml_path=sample_yaml_file)
        gen.client = SimpleNamespace(
            messages=SimpleNamespace(
                create=MagicMock(
                    return_value=_make_anthropic_response(
                        '{"opening_hook": "Dear hiring manager", "professional_summary": "Experienced engineer"}'
                    )
                )
            )
        )

        # Mock input to return values
        mocker.patch("builtins.input", return_value="I am excited about this role.")

        job_desc = "Looking for senior engineer"
        outputs, job_details = gen.generate_interactive(job_desc, company_name="Acme Corp")

        assert isinstance(outputs, dict)
        assert "md" in outputs
        assert job_details["company"] == "Acme Corp"


class TestGenerateNonInteractive:
    """Test generate_non_interactive method."""

    def test_generate_non_interactive(self, sample_yaml_file: Path, monkeypatch):
        """Test non-interactive generation."""
        monkeypatch.setenv("AI_PROVIDER", "anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        gen = CoverLetterGenerator(yaml_path=sample_yaml_file)
        gen.client = SimpleNamespace(
            messages=SimpleNamespace(
                create=MagicMock(
                    return_value=_make_anthropic_response(
                        '{"opening_hook": "Dear hiring manager", "professional_summary": "Summary"}'
                    )
                )
            )
        )

        job_desc = "Looking for engineer"
        outputs, job_details = gen.generate_non_interactive(job_desc, company_name="Acme Corp")

        assert isinstance(outputs, dict)
        assert "md" in outputs
        assert job_details["company"] == "Acme Corp"


class TestRenderTemplate:
    """Test _render_template method."""

    def test_render_template_markdown(self, sample_yaml_file: Path):
        """Test rendering markdown template."""
        gen = CoverLetterGenerator(yaml_path=sample_yaml_file)

        content = {
            "opening_hook": "Dear hiring manager",
            "professional_summary": "Experienced engineer",
            "key_achievements": ["Achievement 1", "Achievement 2"],
            "skills_highlight": ["Python", "Django"],
            "company_alignment": None,
            "connection": None,
        }

        job_details = {"company": "Acme", "position": "Engineer"}

        rendered = gen._render_template(content, job_details)

        assert isinstance(rendered, str)
        assert "Acme" in rendered
        assert "Engineer" in rendered
        assert "Dear hiring manager" in rendered


class TestCompilePdf:
    """Test _compile_pdf method."""

    @patch("subprocess.Popen")
    def test_compile_pdf_success(self, mock_popen, sample_yaml_file: Path, temp_dir: Path):
        """Test PDF compilation succeeds."""
        gen = CoverLetterGenerator(yaml_path=sample_yaml_file)
        output_path = temp_dir / "cover-letter.pdf"
        tex_content = r"\documentclass{article}\begin{document}Test\end{document}"

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"", b"")
        mock_popen.return_value = mock_process

        # Mock file creation
        output_path.write_bytes(b"PDF content")

        result = gen._compile_pdf(output_path, tex_content)

        assert result is True

    @patch("subprocess.Popen", side_effect=FileNotFoundError)
    def test_compile_pdf_failure(self, mock_popen, sample_yaml_file: Path, temp_dir: Path):
        """Test PDF compilation fails gracefully."""
        gen = CoverLetterGenerator(yaml_path=sample_yaml_file)
        output_path = temp_dir / "cover-letter.pdf"
        tex_content = r"\documentclass{article}\begin{document}Test\end{document}"

        result = gen._compile_pdf(output_path, tex_content)

        assert result is False


class TestClearCache:
    """Test clear_cache method."""

    def test_clear_cache_clears_dict(self, sample_yaml_file: Path, monkeypatch):
        """Test clear_cache empties the cache."""
        monkeypatch.setenv("AI_PROVIDER", "anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        gen = CoverLetterGenerator(yaml_path=sample_yaml_file)

        # Add something to cache
        gen._content_cache["test_key"] = "test_value"

        gen.clear_cache()

        assert len(gen._content_cache) == 0


class TestGenerateCoverLetterFunction:
    """Test generate_cover_letter function."""

    def test_generate_cover_letter_interactive(self, sample_yaml_file: Path, monkeypatch, mocker):
        """Test generate_cover_letter in interactive mode."""
        monkeypatch.setenv("AI_PROVIDER", "anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        mocker.patch("builtins.input", return_value="Excited about role")

        outputs, job_details = generate_cover_letter(
            job_description="Job description",
            company_name="Acme",
            yaml_path=sample_yaml_file,
            interactive=True,
        )

        assert isinstance(outputs, dict)
        assert job_details["company"] == "Acme"

    def test_generate_cover_letter_non_interactive(self, sample_yaml_file: Path, monkeypatch):
        """Test generate_cover_letter in non-interactive mode."""
        monkeypatch.setenv("AI_PROVIDER", "anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        outputs, job_details = generate_cover_letter(
            job_description="Job description",
            company_name="Acme",
            yaml_path=sample_yaml_file,
            interactive=False,
        )

        assert isinstance(outputs, dict)
        assert job_details["company"] == "Acme"
