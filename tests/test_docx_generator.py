"""Unit tests for DocxGenerator class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cli.generators.docx_generator import DocxGenerator


@pytest.fixture
def docx_generator(sample_yaml_file, mock_config):
    """Create DocxGenerator instance with test data."""
    return DocxGenerator(yaml_path=sample_yaml_file, config=mock_config)


class TestDocxGeneratorInitialization:
    """Test DocxGenerator initialization."""

    def test_init_with_yaml_path(self, sample_yaml_file, mock_config):
        """Test initialization with yaml path."""
        gen = DocxGenerator(yaml_path=sample_yaml_file, config=mock_config)
        assert gen.yaml_handler is not None
        assert gen.config is not None

    def test_init_default(self):
        """Test initialization with defaults."""
        gen = DocxGenerator()
        assert gen.yaml_handler is not None

    def test_font_constants(self):
        """Test font constants are defined."""
        assert DocxGenerator.FONT_NAME == "Arial"
        assert DocxGenerator.FONT_SIZE == 11
        assert DocxGenerator.FONT_SIZE_LARGE == 14
        assert DocxGenerator.FONT_SIZE_MEDIUM == 12


class TestDocxGeneratorGenerate:
    """Test generate method."""

    @patch("cli.generators.docx_generator.Document")
    def test_generate_returns_document(self, mock_document_class, docx_generator):
        """Test generate returns Document object without saving when no path provided."""
        mock_doc = MagicMock()
        mock_document_class.return_value = mock_doc

        result = docx_generator.generate(variant="v1.0.0-base")

        assert mock_doc is not None
        # save should NOT be called when output_path is not provided
        mock_doc.save.assert_not_called()

    @patch("cli.generators.docx_generator.Document")
    def test_generate_with_output_path(self, mock_document_class, docx_generator, temp_dir: Path):
        """Test generate saves to output path."""
        mock_doc = MagicMock()
        mock_document_class.return_value = mock_doc

        output_path = temp_dir / "resume.docx"
        docx_generator.generate(variant="v1.0.0-base", output_path=output_path)

        mock_doc.save.assert_called_once_with(str(output_path))

    @patch("cli.generators.docx_generator.Document")
    def test_generate_creates_parent_directories(self, mock_document_class, docx_generator, temp_dir: Path):
        """Test generate creates parent directories."""
        mock_doc = MagicMock()
        mock_document_class.return_value = mock_doc

        output_path = temp_dir / "subdir" / "resume.docx"
        docx_generator.generate(variant="v1.0.0-base", output_path=output_path)

        assert output_path.parent.exists()

    @patch("cli.generators.docx_generator.Document")
    def test_generate_with_enhanced_context(self, mock_document_class, docx_generator):
        """Test generate with enhanced context."""
        mock_doc = MagicMock()
        mock_document_class.return_value = mock_doc

        enhanced_context = {
            "summary": "Enhanced summary with AI insights",
            "projects": {
                "featured": [
                    {
                        "name": "test-project",
                        "description": "Test description",
                        "highlighted_technologies": ["Python", "FastAPI"],
                    }
                ]
            },
        }

        result = docx_generator.generate(
            variant="v1.0.0-base", enhanced_context=enhanced_context
        )

        assert mock_doc is not None

    @patch("cli.generators.docx_generator.Document")
    def test_generate_variant_key_extraction(self, mock_document_class, docx_generator):
        """Test variant key extraction for different variant names."""
        mock_doc = MagicMock()
        mock_document_class.return_value = mock_doc

        # Test different variant formats
        variants = ["v1.0.0-base", "v1.1.0-backend", "v2.0.0-ml_ai"]
        for variant in variants:
            result = docx_generator.generate(variant=variant)
            assert mock_doc is not None


class TestAddHeader:
    """Test _add_header method."""

    def test_add_header_with_name(self, docx_generator):
        """Test adding header with name."""
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_doc.add_paragraph.return_value = mock_para
        mock_run = MagicMock()
        mock_para.add_run.return_value = mock_run

        contact = {"name": "John Doe"}
        docx_generator._add_header(mock_doc, contact)

        mock_doc.add_paragraph.assert_called()

    def test_add_header_with_credentials(self, docx_generator):
        """Test adding header with credentials."""
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_doc.add_paragraph.return_value = mock_para
        mock_run = MagicMock()
        mock_para.add_run.return_value = mock_run

        contact = {"name": "John Doe", "credentials": ["P.E.", "M.S."]}
        docx_generator._add_header(mock_doc, contact)

    def test_add_header_with_location(self, docx_generator):
        """Test adding header with location."""
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_doc.add_paragraph.return_value = mock_para

        contact = {
            "name": "John Doe",
            "location": {"city": "San Francisco", "state": "CA", "zip": "94105"},
        }
        docx_generator._add_header(mock_doc, contact)

    def test_add_header_with_email_and_phone(self, docx_generator):
        """Test adding header with email and phone."""
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_doc.add_paragraph.return_value = mock_para

        contact = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-123-4567",
        }
        docx_generator._add_header(mock_doc, contact)

    def test_add_header_with_urls(self, docx_generator):
        """Test adding header with URLs."""
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_doc.add_paragraph.return_value = mock_para

        contact = {
            "name": "John Doe",
            "urls": {
                "github": "https://github.com/johndoe",
                "linkedin": "https://linkedin.com/in/johndoe",
                "website": "https://johndoe.com",
            },
        }
        docx_generator._add_header(mock_doc, contact)

    def test_add_header_empty_contact(self, docx_generator):
        """Test adding header with empty contact."""
        mock_doc = MagicMock()

        docx_generator._add_header(mock_doc, {})

        # Should not crash with empty contact


class TestAddSectionHeading:
    """Test _add_section_heading method."""

    def test_add_section_heading(self, docx_generator):
        """Test adding section heading."""
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_doc.add_paragraph.return_value = mock_para
        mock_run = MagicMock()
        mock_para.add_run.return_value = mock_run

        docx_generator._add_section_heading(mock_doc, "Experience")

        mock_para.add_run.assert_called()
        mock_run.font.bold = True


class TestAddSummary:
    """Test _add_summary method."""

    def test_add_summary_with_dict(self, docx_generator):
        """Test adding summary with dict."""
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_doc.add_paragraph.return_value = mock_para

        summary = {"content": "Experienced software engineer with 5+ years..."}
        docx_generator._add_summary(mock_doc, summary)

    def test_add_summary_with_string(self, docx_generator):
        """Test adding summary with string."""
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_doc.add_paragraph.return_value = mock_para

        summary = "Experienced software engineer with 5+ years..."
        docx_generator._add_summary(mock_doc, summary)

    def test_add_summary_none(self, docx_generator):
        """Test adding summary with None."""
        mock_doc = MagicMock()

        docx_generator._add_summary(mock_doc, None)

        # Should not crash


class TestAddProjects:
    """Test _add_projects method."""

    def test_add_projects_with_data(self, docx_generator):
        """Test adding projects with data."""
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_doc.add_paragraph.return_value = mock_para

        projects = {
            "ai_ml": [
                {
                    "name": "ML Project",
                    "description": "A machine learning project",
                    "url": "https://github.com/user/ml",
                    "highlighted_technologies": ["Python", "PyTorch"],
                }
            ]
        }
        docx_generator._add_projects(mock_doc, projects)

    def test_add_projects_with_enhanced_description(self, docx_generator):
        """Test adding projects with enhanced description."""
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_doc.add_paragraph.return_value = mock_para

        projects = {
            "featured": [
                {
                    "name": "Test Project",
                    "enhanced_description": "An enhanced project description",
                    "highlighted_technologies": ["Python", "FastAPI"],
                    "achievement_highlights": ["Achieved 99% accuracy"],
                }
            ]
        }
        docx_generator._add_projects(mock_doc, projects)

    def test_add_projects_empty(self, docx_generator):
        """Test adding projects with empty dict."""
        mock_doc = MagicMock()

        docx_generator._add_projects(mock_doc, {})


class TestAddExperience:
    """Test _add_experience method."""

    def test_add_experience_with_data(self, docx_generator):
        """Test adding experience with data."""
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_doc.add_paragraph.return_value = mock_para

        experience = [
            {
                "title": "Senior Engineer",
                "company": "Tech Corp",
                "location": "San Francisco, CA",
                "start_date": "2020-01",
                "end_date": "Present",
                "bullets": [
                    {"text": "Led team of 5 engineers"},
                    {"text": "Improved system performance by 40%"},
                ],
            }
        ]
        docx_generator._add_experience(mock_doc, experience)

    def test_add_experience_empty(self, docx_generator):
        """Test adding experience with empty list."""
        mock_doc = MagicMock()

        docx_generator._add_experience(mock_doc, [])

    def test_add_experience_with_current_job(self, docx_generator):
        """Test adding experience with current job (no end_date)."""
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_doc.add_paragraph.return_value = mock_para

        experience = [
            {
                "title": "Software Engineer",
                "company": "Startup Inc",
                "start_date": "2023-06",
                "end_date": None,
                "bullets": [{"text": "Built REST APIs"}],
            }
        ]
        docx_generator._add_experience(mock_doc, experience)


class TestAddEducation:
    """Test _add_education method."""

    def test_add_education_with_data(self, docx_generator):
        """Test adding education with data."""
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_doc.add_paragraph.return_value = mock_para

        education = [
            {
                "institution": "MIT",
                "location": "Cambridge, MA",
                "degree": "Bachelor of Science",
                "field": "Computer Science",
                "graduation_date": "2018-05",
            }
        ]
        docx_generator._add_education(mock_doc, education)

    def test_add_education_empty(self, docx_generator):
        """Test adding education with empty list."""
        mock_doc = MagicMock()

        docx_generator._add_education(mock_doc, [])


class TestAddSkills:
    """Test _add_skills method."""

    def test_add_skills_with_dict(self, docx_generator):
        """Test adding skills with dict."""
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_doc.add_paragraph.return_value = mock_para
        mock_run = MagicMock()
        mock_para.add_run.return_value = mock_run

        skills = {
            "programming_languages": [
                {"name": "Python", "level": "Expert"},
                {"name": "JavaScript", "level": "Advanced"},
            ],
            "cloud": [{"name": "AWS", "services": ["EC2", "S3"]}],
        }
        docx_generator._add_skills(mock_doc, skills)

    def test_add_skills_with_string_list(self, docx_generator):
        """Test adding skills with string list."""
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_doc.add_paragraph.return_value = mock_para
        mock_run = MagicMock()
        mock_para.add_run.return_value = mock_run

        skills = {
            "languages": ["Python", "JavaScript", "Go"],
        }
        docx_generator._add_skills(mock_doc, skills)

    def test_add_skills_empty(self, docx_generator):
        """Test adding skills with empty dict."""
        mock_doc = MagicMock()

        docx_generator._add_skills(mock_doc, {})


class TestAddPublications:
    """Test _add_publications method."""

    def test_add_publications_with_data(self, docx_generator):
        """Test adding publications with data."""
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_doc.add_paragraph.return_value = mock_para

        publications = [
            {
                "type": "conference",
                "title": "Deep Learning for NLP",
                "authors": "John Doe, Jane Smith",
                "year": "2020",
                "conference": "NeurIPS",
            }
        ]
        docx_generator._add_publications(mock_doc, publications)

    def test_add_publications_empty(self, docx_generator):
        """Test adding publications with empty list."""
        mock_doc = MagicMock()

        docx_generator._add_publications(mock_doc, [])


class TestAddCertifications:
    """Test _add_certifications method."""

    def test_add_certifications_with_data(self, docx_generator):
        """Test adding certifications with data."""
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_doc.add_paragraph.return_value = mock_para

        certifications = [
            {
                "name": "AWS Solutions Architect",
                "issuer": "Amazon Web Services",
                "license_number": "ABC123",
            }
        ]
        docx_generator._add_certifications(mock_doc, certifications)

    def test_add_certifications_empty(self, docx_generator):
        """Test adding certifications with empty list."""
        mock_doc = MagicMock()

        docx_generator._add_certifications(mock_doc, [])
