"""Unit tests for KeywordDensityGenerator class."""

import json
from pathlib import Path

import pytest

from cli.generators.keyword_density import (
    KeywordDensityGenerator,
    KeywordDensityReport,
    KeywordInfo,
)


@pytest.fixture
def keyword_generator(sample_yaml_file: Path, mock_config):
    """Create KeywordDensityGenerator instance with test data."""
    return KeywordDensityGenerator(yaml_path=sample_yaml_file, config=mock_config)


class TestKeywordDensityGeneratorInitialization:
    """Test KeywordDensityGenerator initialization."""

    def test_init_with_yaml_path(self, sample_yaml_file: Path, mock_config):
        """Test initialization with yaml path."""
        gen = KeywordDensityGenerator(yaml_path=sample_yaml_file, config=mock_config)
        assert gen.yaml_path == sample_yaml_file

    def test_init_default(self):
        """Test initialization with defaults."""
        gen = KeywordDensityGenerator()
        assert gen.yaml_handler is not None


class TestGenerateReport:
    """Test generate_report method."""

    def test_generate_report_returns_report(self, keyword_generator):
        """Test generate_report returns KeywordDensityReport."""
        job_desc = "We need a Python developer with Kubernetes and AWS experience."

        report = keyword_generator.generate_report(job_desc, variant="v1.0.0-base")

        assert isinstance(report, KeywordDensityReport)

    def test_generate_report_with_variant(self, keyword_generator):
        """Test generate_report with variant parameter."""
        job_desc = "Python JavaScript React"

        report = keyword_generator.generate_report(job_desc, variant="v1.1.0-backend")

        assert report.job_title or report.company

    def test_generate_report_calculates_density(self, keyword_generator):
        """Test density score calculation."""
        job_desc = "Python Kubernetes AWS Docker"

        report = keyword_generator.generate_report(job_desc)

        assert 0 <= report.density_score <= 100


class TestExtractJobDetails:
    """Test _extract_job_details method."""

    def test_extract_job_title(self, keyword_generator):
        """Test extracting job title from description."""
        job_desc = """
        Job Title: Senior Software Engineer
        Company: Tech Corp
        We are looking for a developer.
        """

        title, company = keyword_generator._extract_job_details(job_desc)

        assert title

    def test_extract_company(self, keyword_generator):
        """Test extracting company from description."""
        job_desc = "Software Engineer\nCompany: Acme Corp\nWe need a developer."

        title, company = keyword_generator._extract_job_details(job_desc)

        assert company


class TestExtractJobKeywords:
    """Test _extract_job_keywords method."""

    def test_extract_job_keywords_fallback(self, keyword_generator):
        """Test job keyword extraction uses fallback."""
        job_desc = "Python JavaScript React Kubernetes AWS"

        keywords = keyword_generator._extract_job_keywords(job_desc)

        assert isinstance(keywords, list)
        assert len(keywords) > 0

    def test_extract_job_keywords_with_importance(self, keyword_generator):
        """Test keyword extraction includes importance levels."""
        job_desc = "Python and JavaScript required. Kubernetes nice to have."

        keywords = keyword_generator._extract_job_keywords(job_desc)

        # Each keyword should have importance
        for kw, importance in keywords:
            assert importance in ["high", "medium", "low"]


class TestSimpleKeywordExtraction:
    """Test _simple_keyword_extraction fallback method."""

    def test_simple_extraction_finds_keywords(self, keyword_generator):
        """Test simple keyword extraction finds common keywords."""
        job_desc = "We need a Python developer with Kubernetes, Docker, and AWS experience."

        keywords = keyword_generator._simple_keyword_extraction(job_desc)

        assert isinstance(keywords, list)
        # Should find keywords as tuples (keyword, importance)
        for kw, imp in keywords:
            assert isinstance(kw, str)
            assert isinstance(imp, str)


class TestGetResumeData:
    """Test _get_resume_data method."""

    def test_get_resume_data(self, keyword_generator):
        """Test getting resume data."""
        data = keyword_generator._get_resume_data("v1.0.0-base")

        assert "skills" in data
        assert "experience" in data
        assert "summary" in data


class TestCountKeywordsInResume:
    """Test _count_keywords_in_resume method."""

    def test_count_keywords(self, keyword_generator):
        """Test counting keywords in resume."""
        keywords = [("python", "high"), ("javascript", "high")]
        resume_data = {
            "skills": {"programming": ["Python", "JavaScript"]},
            "experience": [],
            "summary": "Python developer",
        }

        counts = keyword_generator._count_keywords_in_resume(keywords, resume_data)

        assert "python" in counts
        assert counts["python"] > 0


class TestGetAllText:
    """Test _get_all_text helper method."""

    def test_get_all_text_from_nested_dict(self, keyword_generator):
        """Test extracting text from nested dictionary."""
        resume_data = {
            "skills": {"programming": ["Python"]},
            "experience": [
                {
                    "company": "Tech Corp",
                    "bullets": [{"text": "Built APIs"}],
                }
            ],
            "summary": "Experienced developer",
        }

        text = keyword_generator._get_all_text(resume_data)

        assert "Python" in text
        assert "Tech Corp" in text
        assert "Built APIs" in text


class TestSuggestSectionsForKeyword:
    """Test _suggest_sections_for_keyword method."""

    def test_suggest_for_missing_keyword(self, keyword_generator):
        """Test suggesting sections for missing keyword."""
        resume_data = {"skills": {}, "experience": []}

        suggestions = keyword_generator._suggest_sections_for_keyword(
            "python", resume_data, is_present=False
        )

        assert len(suggestions) > 0

    def test_no_suggestion_for_present_keyword(self, keyword_generator):
        """Test no suggestion for present keyword."""
        resume_data = {"skills": {"programming": ["Python"]}, "experience": []}

        suggestions = keyword_generator._suggest_sections_for_keyword(
            "python", resume_data, is_present=True
        )

        assert suggestions == []


class TestGenerateSuggestions:
    """Test _generate_suggestions method."""

    def test_generate_suggestions_high_importance(self, keyword_generator):
        """Test generating suggestions for high importance missing keywords."""
        missing = [
            KeywordInfo("python", "high", 0, False, ["Skills"]),
            KeywordInfo("kubernetes", "medium", 0, False, ["Experience"]),
        ]

        suggestions = keyword_generator._generate_suggestions(missing)

        assert len(suggestions) > 0

    def test_generate_suggestions_empty(self, keyword_generator):
        """Test generating suggestions with empty list."""
        suggestions = keyword_generator._generate_suggestions([])

        assert suggestions == []


class TestPrintReport:
    """Test print_report method."""

    def test_print_report_no_error(self, keyword_generator, capsys):
        """Test print_report runs without error."""
        report = KeywordDensityReport(
            job_title="Engineer",
            company="Test Corp",
            top_keywords=[
                KeywordInfo("python", "high", 5, True, ["Skills"]),
                KeywordInfo("kubernetes", "medium", 0, False, ["Skills"]),
            ],
            density_score=50,
            present_count=1,
            missing_count=1,
            suggestions=["Add kubernetes"],
        )

        keyword_generator.print_report(report)

        captured = capsys.readouterr()
        assert "Keyword" in captured.out or "Engineer" in captured.out


class TestExportJSON:
    """Test export_json method."""

    def test_export_json_creates_file(self, keyword_generator, temp_dir: Path):
        """Test export_json creates JSON file."""
        report = KeywordDensityReport(
            job_title="Engineer",
            company="Test Corp",
            top_keywords=[
                KeywordInfo("python", "high", 5, True, ["Skills"]),
            ],
            density_score=100,
            present_count=1,
            missing_count=0,
            suggestions=[],
        )

        output_path = temp_dir / "report.json"
        keyword_generator.export_json(report, output_path)

        assert output_path.exists()

        # Verify JSON content
        with open(output_path) as f:
            data = json.load(f)

        assert data["job_title"] == "Engineer"
        assert data["density_score"] == 100
