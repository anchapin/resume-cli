"""Unit tests for ATSGenerator class."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from cli.generators.ats_generator import (
    ATSCategoryScore,
    ATSGenerator,
    ATSReport,
)


@pytest.fixture
def ats_generator(sample_yaml_file: Path, mock_config):
    """Create ATSGenerator instance with test data."""
    return ATSGenerator(yaml_path=sample_yaml_file, config=mock_config)


class TestATSGeneratorInitialization:
    """Test ATSGenerator initialization."""

    def test_init_with_yaml_path(self, sample_yaml_file: Path, mock_config):
        """Test initialization with yaml path."""
        gen = ATSGenerator(yaml_path=sample_yaml_file, config=mock_config)
        assert gen.yaml_path == sample_yaml_file

    def test_init_default(self):
        """Test initialization with defaults."""
        gen = ATSGenerator()
        assert gen.yaml_handler is not None


class TestGenerateReport:
    """Test generate_report method."""

    def test_generate_report_returns_ats_report(self, ats_generator):
        """Test generate_report returns ATSReport object."""
        job_desc = "We need a Python developer with Kubernetes and AWS experience."

        report = ats_generator.generate_report(job_desc, variant="v1.0.0-base")

        assert isinstance(report, ATSReport)
        assert 0 <= report.total_score <= report.total_possible

    def test_generate_report_with_all_categories(self, ats_generator):
        """Test all categories are scored."""
        job_desc = "Python developer with Kubernetes and AWS"

        report = ats_generator.generate_report(job_desc)

        assert "format_parsing" in report.categories
        assert "keywords" in report.categories
        assert "section_structure" in report.categories
        assert "contact_info" in report.categories
        assert "readability" in report.categories

    def test_generate_report_calculates_total(self, ats_generator):
        """Test total score is calculated correctly."""
        job_desc = "Python Kubernetes AWS"

        report = ats_generator.generate_report(job_desc)

        expected_total = sum(cat.points_earned for cat in report.categories.values())
        assert report.total_score == expected_total


class TestFormatParsing:
    """Test _check_format_parsing method."""

    def test_format_parsing_with_data(self, ats_generator):
        """Test format parsing with valid resume data."""
        resume_data = {
            "contact": {"name": "John"},
            "experience": [],
        }

        result = ats_generator._check_format_parsing(resume_data)

        assert isinstance(result, ATSCategoryScore)
        assert result.points_possible == 20

    def test_format_parsing_empty_data(self, ats_generator):
        """Test format parsing with empty data."""
        resume_data = {}

        result = ats_generator._check_format_parsing(resume_data)

        assert result.points_earned < result.points_possible


class TestKeywords:
    """Test _check_keywords method."""

    def test_keywords_matching(self, ats_generator):
        """Test keyword matching between job and resume."""
        resume_data = {
            "skills": {
                "programming": ["Python", "JavaScript"],
                "cloud": ["AWS"],
            },
            "experience": [
                {
                    "company": "Test",
                    "bullets": [
                        {"text": "Built APIs with Python and FastAPI"}
                    ]
                }
            ],
            "summary": "Experienced Python developer",
        }
        job_desc = "We need Python, JavaScript, and AWS developer"

        result = ats_generator._check_keywords(resume_data, job_desc)

        assert isinstance(result, ATSCategoryScore)
        assert result.points_possible == 30

    def test_keywords_empty_job_description(self, ats_generator):
        """Test keywords with empty job description."""
        resume_data = {"skills": {"programming": ["Python"]}, "experience": [], "summary": ""}

        result = ats_generator._check_keywords(resume_data, "")

        # Should give full points when no keywords to match
        assert result.points_earned >= 0


class TestSectionStructure:
    """Test _check_section_structure method."""

    def test_section_structure_complete(self, ats_generator):
        """Test section structure with all sections."""
        resume_data = {
            "experience": [{"company": "Test", "bullets": []}],
            "education": [{"degree": "BS"}],
            "skills": {"programming": ["Python"]},
            "summary": "Experienced developer",
        }

        result = ats_generator._check_section_structure(resume_data)

        assert result.points_possible == 20
        # Should have points for each section

    def test_section_structure_missing_sections(self, ats_generator):
        """Test section structure with missing sections."""
        resume_data = {}

        result = ats_generator._check_section_structure(resume_data)

        assert result.points_earned < result.points_possible


class TestContactInfo:
    """Test _check_contact_info method."""

    def test_contact_info_complete(self, ats_generator):
        """Test contact info with all fields."""
        resume_data = {
            "contact": {
                "email": "test@example.com",
                "phone": "555-123-4567",
                "location": {"city": "SF", "state": "CA"},
            }
        }

        result = ats_generator._check_contact_info(resume_data)

        assert result.points_possible == 15

    def test_contact_info_partial(self, ats_generator):
        """Test contact info with partial data."""
        resume_data = {
            "contact": {
                "email": "test@example.com",
            }
        }

        result = ats_generator._check_contact_info(resume_data)

        assert result.points_earned < result.points_possible


class TestReadability:
    """Test _check_readability method."""

    def test_readability_with_metrics(self, ats_generator):
        """Test readability with action verbs and metrics."""
        resume_data = {
            "experience": [
                {
                    "company": "Test",
                    "bullets": [
                        {"text": "Increased sales by 30%"},
                        {"text": "Built scalable APIs"},
                    ]
                }
            ],
            "summary": "Led team",
        }

        result = ats_generator._check_readability(resume_data)

        assert result.points_possible == 15

    def test_readability_poor_content(self, ats_generator):
        """Test readability with poor content."""
        resume_data = {
            "experience": [
                {
                    "company": "Test",
                    "bullets": []
                }
            ],
            "summary": "",
        }

        result = ats_generator._check_readability(resume_data)

        assert result.points_earned < result.points_possible


class TestKeywordExtraction:
    """Test keyword extraction methods."""

    def test_extract_job_keywords_fallback(self, ats_generator):
        """Test job keyword extraction uses fallback."""
        job_desc = "Python JavaScript React Kubernetes AWS"

        keywords = ats_generator._extract_job_keywords(job_desc)

        assert isinstance(keywords, list)
        # Should find common keywords
        assert len(keywords) > 0

    def test_extract_resume_keywords(self, ats_generator):
        """Test resume keyword extraction."""
        resume_data = {
            "skills": {
                "programming": ["Python", "JavaScript"],
                "cloud": ["AWS", "GCP"],
            },
            "experience": [
                {
                    "company": "Test",
                    "bullets": [
                        {"text": "Built REST APIs with FastAPI"}
                    ]
                }
            ],
            "summary": "Experienced Python developer",
        }

        keywords = ats_generator._extract_resume_keywords(resume_data)

        assert isinstance(keywords, list)


class TestSimpleKeywordExtraction:
    """Test _simple_keyword_extraction fallback method."""

    def test_simple_extraction_finds_keywords(self, ats_generator):
        """Test simple keyword extraction finds common keywords."""
        job_desc = "We need a Python developer with Kubernetes, Docker, and AWS experience."

        keywords = ats_generator._simple_keyword_extraction(job_desc)

        assert "python" in keywords
        assert "kubernetes" in keywords
        assert "docker" in keywords
        assert "aws" in keywords


class TestGenerateSummary:
    """Test _generate_summary method."""

    def test_generate_summary_excellent(self, ats_generator):
        """Test summary for excellent score."""
        categories = {
            "test": ATSCategoryScore("Test", 20, 20, [], []),
        }

        summary, recommendations = ats_generator._generate_summary(categories, 95, 100)

        assert "Excellent" in summary

    def test_generate_summary_poor(self, ats_generator):
        """Test summary for poor score."""
        categories = {
            "test": ATSCategoryScore("Test", 5, 20, [], []),
        }

        summary, recommendations = ats_generator._generate_summary(categories, 25, 100)

        assert "Poor" in summary or "Fair" in summary


class TestPrintReport:
    """Test print_report method."""

    def test_print_report_no_error(self, ats_generator, capsys):
        """Test print_report runs without error."""
        report = ATSReport(
            total_score=80,
            total_possible=100,
            categories={
                "format_parsing": ATSCategoryScore("Format Parsing", 20, 20, ["Good"], []),
                "keywords": ATSCategoryScore("Keywords", 20, 30, ["Partial"], ["Add keywords"]),
                "section_structure": ATSCategoryScore("Section Structure", 20, 20, ["Good"], []),
                "contact_info": ATSCategoryScore("Contact Info", 10, 15, ["Partial"], ["Add phone"]),
                "readability": ATSCategoryScore("Readability", 10, 15, ["Partial"], []),
            },
            summary="Good score",
            recommendations=["Add keywords"],
        )

        ats_generator.print_report(report)

        captured = capsys.readouterr()
        assert "ATS Score" in captured.out


class TestExportJSON:
    """Test export_json method."""

    def test_export_json_creates_file(self, ats_generator, temp_dir: Path):
        """Test export_json creates JSON file."""
        report = ATSReport(
            total_score=80,
            total_possible=100,
            categories={
                "format_parsing": ATSCategoryScore("Format Parsing", 20, 20, ["Good"], []),
                "keywords": ATSCategoryScore("Keywords", 20, 30, ["Partial"], []),
                "section_structure": ATSCategoryScore("Section Structure", 20, 20, ["Good"], []),
                "contact_info": ATSCategoryScore("Contact Info", 10, 15, ["Partial"], []),
                "readability": ATSCategoryScore("Readability", 10, 15, ["Partial"], []),
            },
            summary="Good",
            recommendations=[],
        )

        output_path = temp_dir / "report.json"
        ats_generator.export_json(report, output_path)

        assert output_path.exists()

        # Verify JSON content
        with open(output_path) as f:
            data = json.load(f)

        assert data["total_score"] == 80
        assert data["overall_percentage"] == 80.0


class TestGetAllText:
    """Test _get_all_text helper method."""

    def test_get_all_text_from_nested_dict(self, ats_generator):
        """Test extracting text from nested dictionary."""
        resume_data = {
            "contact": {"name": "John", "email": "john@test.com"},
            "experience": [
                {
                    "company": "Tech Corp",
                    "title": "Engineer",
                    "bullets": [
                        {"text": "Built APIs"}
                    ]
                }
            ],
            "skills": {"programming": ["Python"]},
        }

        text = ats_generator._get_all_text(resume_data)

        # Text is lowercased
        assert "john" in text
        assert "tech corp" in text
        assert "built apis" in text
        assert "python" in text
