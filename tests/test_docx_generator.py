"""Tests for DOCX resume generator."""

from unittest.mock import MagicMock, patch


class TestDocxGeneratorInitialization:
    """Tests for DocxGenerator initialization."""

    def test_init_with_yaml_path(self, sample_yaml_file):
        """Test initialization with yaml_path."""
        from cli.generators.docx_generator import DocxGenerator

        generator = DocxGenerator(yaml_path=sample_yaml_file)
        assert generator.yaml_handler is not None
        assert generator.config is not None

    def test_init_with_config(self, sample_yaml_file):
        """Test initialization with config."""
        from cli.generators.docx_generator import DocxGenerator
        from cli.utils.config import Config

        config = Config()
        generator = DocxGenerator(yaml_path=sample_yaml_file, config=config)
        assert generator.config is config

    def test_init_without_params(self):
        """Test initialization without parameters."""
        from cli.generators.docx_generator import DocxGenerator

        generator = DocxGenerator()
        assert generator.yaml_handler is not None
        assert generator.config is not None

    def test_font_constants(self):
        """Test font constants are defined."""
        from cli.generators.docx_generator import DocxGenerator

        assert DocxGenerator.FONT_NAME == "Arial"
        assert DocxGenerator.FONT_SIZE == 11
        assert DocxGenerator.FONT_SIZE_LARGE == 14
        assert DocxGenerator.FONT_SIZE_MEDIUM == 12


class TestDocxGeneratorGenerate:
    """Tests for DocxGenerator.generate method."""

    @patch("cli.generators.docx_generator.Document")
    def test_generate_basic(self, mock_document, sample_yaml_file):
        """Test basic generate call."""
        from cli.generators.docx_generator import DocxGenerator

        # Setup mocks
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        mock_doc.styles = {"Normal": MagicMock()}
        mock_doc.add_paragraph = MagicMock(return_value=MagicMock())

        generator = DocxGenerator(yaml_path=sample_yaml_file)
        result = generator.generate(variant="v1.0.0-base")

        assert result is mock_doc

    @patch("cli.generators.docx_generator.Document")
    def test_generate_with_output_path(self, mock_document, sample_yaml_file, temp_dir):
        """Test generate with output path."""
        from cli.generators.docx_generator import DocxGenerator

        # Setup mocks
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        mock_doc.styles = {"Normal": MagicMock()}
        mock_doc.add_paragraph = MagicMock(return_value=MagicMock())

        output_path = temp_dir / "resume.docx"
        generator = DocxGenerator(yaml_path=sample_yaml_file)
        result = generator.generate(variant="v1.0.0-base", output_path=output_path)

        assert result is mock_doc
        mock_doc.save.assert_called_once()

    @patch("cli.generators.docx_generator.Document")
    def test_generate_backend_variant(self, mock_document, sample_yaml_file):
        """Test generate with backend variant."""
        from cli.generators.docx_generator import DocxGenerator

        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        mock_doc.styles = {"Normal": MagicMock()}
        mock_doc.add_paragraph = MagicMock(return_value=MagicMock())

        generator = DocxGenerator(yaml_path=sample_yaml_file)
        result = generator.generate(variant="v1.1.0-backend")

        assert result is mock_doc

    @patch("cli.generators.docx_generator.Document")
    def test_generate_ml_ai_variant(self, mock_document, sample_yaml_file):
        """Test generate with ML/AI variant."""
        from cli.generators.docx_generator import DocxGenerator

        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        mock_doc.styles = {"Normal": MagicMock()}
        mock_doc.add_paragraph = MagicMock(return_value=MagicMock())

        generator = DocxGenerator(yaml_path=sample_yaml_file)
        result = generator.generate(variant="v1.2.0-ml_ai")

        assert result is mock_doc

    @patch("cli.generators.docx_generator.Document")
    def test_generate_with_enhanced_context(self, mock_document, sample_yaml_file):
        """Test generate with enhanced context."""
        from cli.generators.docx_generator import DocxGenerator

        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        mock_doc.styles = {"Normal": MagicMock()}
        mock_doc.add_paragraph = MagicMock(return_value=MagicMock())

        enhanced_context = {
            "summary": "Enhanced summary with AI improvements",
            "projects": {
                "featured": [
                    {
                        "name": "Test Project",
                        "highlighted_technologies": ["Python", "FastAPI"],
                        "enhanced_description": "Test description",
                    }
                ]
            },
        }

        generator = DocxGenerator(yaml_path=sample_yaml_file)
        result = generator.generate(variant="v1.0.0-base", enhanced_context=enhanced_context)

        assert result is mock_doc


class TestDocxGeneratorAddHeader:
    """Tests for _add_header method."""

    @patch("cli.generators.docx_generator.Document")
    def test_add_header_with_name(self, mock_document, sample_yaml_file):
        """Test adding header with name."""
        from cli.generators.docx_generator import DocxGenerator

        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        mock_doc.add_paragraph = MagicMock(return_value=MagicMock())

        generator = DocxGenerator(yaml_path=sample_yaml_file)

        contact = {"name": "John Doe", "email": "john@example.com", "phone": "555-1234"}
        generator._add_header(mock_doc, contact)

        mock_doc.add_paragraph.assert_called()

    @patch("cli.generators.docx_generator.Document")
    def test_add_header_with_location(self, mock_document, sample_yaml_file):
        """Test adding header with location."""
        from cli.generators.docx_generator import DocxGenerator

        mock_doc = MagicMock()
        mock_document.return_value = mock_doc

        generator = DocxGenerator(yaml_path=sample_yaml_file)

        contact = {
            "name": "John Doe",
            "location": {"city": "Boston", "state": "MA"},
            "email": "john@example.com",
        }
        generator._add_header(mock_doc, contact)

    @patch("cli.generators.docx_generator.Document")
    def test_add_header_with_urls(self, mock_document, sample_yaml_file):
        """Test adding header with URLs."""
        from cli.generators.docx_generator import DocxGenerator

        mock_doc = MagicMock()
        mock_document.return_value = mock_doc

        generator = DocxGenerator(yaml_path=sample_yaml_file)

        contact = {
            "name": "John Doe",
            "urls": {
                "github": "https://github.com/johndoe",
                "linkedin": "https://linkedin.com/in/johndoe",
            },
        }
        generator._add_header(mock_doc, contact)

    @patch("cli.generators.docx_generator.Document")
    def test_add_header_with_credentials(self, mock_document, sample_yaml_file):
        """Test adding header with credentials."""
        from cli.generators.docx_generator import DocxGenerator

        mock_doc = MagicMock()
        mock_document.return_value = mock_doc

        generator = DocxGenerator(yaml_path=sample_yaml_file)

        contact = {
            "name": "John Doe",
            "credentials": ["MBA", "PMP"],
        }
        generator._add_header(mock_doc, contact)


class TestDocxGeneratorAddSections:
    """Tests for section adding methods."""

    @patch("cli.generators.docx_generator.Document")
    def test_add_summary(self, mock_document, sample_yaml_file):
        """Test adding summary section."""
        from cli.generators.docx_generator import DocxGenerator

        mock_doc = MagicMock()
        mock_document.return_value = mock_doc

        generator = DocxGenerator(yaml_path=sample_yaml_file)

        summary = {"content": "Experienced professional with 10+ years..."}
        generator._add_summary(mock_doc, summary)

        mock_doc.add_paragraph.assert_called()

    @patch("cli.generators.docx_generator.Document")
    def test_add_summary_empty(self, mock_document, sample_yaml_file):
        """Test adding empty summary."""
        from cli.generators.docx_generator import DocxGenerator

        mock_doc = MagicMock()
        mock_document.return_value = mock_doc

        generator = DocxGenerator(yaml_path=sample_yaml_file)

        generator._add_summary(mock_doc, None)
        generator._add_summary(mock_doc, {})

        # No paragraphs should be added for empty summary

    @patch("cli.generators.docx_generator.Document")
    def test_add_projects(self, mock_document, sample_yaml_file):
        """Test adding projects section."""
        from cli.generators.docx_generator import DocxGenerator

        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        mock_doc.add_paragraph = MagicMock(return_value=MagicMock())

        generator = DocxGenerator(yaml_path=sample_yaml_file)

        projects = {
            "ai_ml": [
                {
                    "name": "Test Project",
                    "description": "A test project",
                    "url": "https://github.com/test",
                }
            ]
        }
        generator._add_projects(mock_doc, projects)

    @patch("cli.generators.docx_generator.Document")
    def test_add_projects_empty(self, mock_document, sample_yaml_file):
        """Test adding empty projects."""
        from cli.generators.docx_generator import DocxGenerator

        mock_doc = MagicMock()
        mock_document.return_value = mock_doc

        generator = DocxGenerator(yaml_path=sample_yaml_file)

        generator._add_projects(mock_doc, None)
        generator._add_projects(mock_doc, {})

    @patch("cli.generators.docx_generator.Document")
    def test_add_experience(self, mock_document, sample_yaml_file):
        """Test adding experience section."""
        from cli.generators.docx_generator import DocxGenerator

        mock_doc = MagicMock()
        mock_document.return_value = mock_doc

        generator = DocxGenerator(yaml_path=sample_yaml_file)

        experience = [
            {
                "title": "Senior Engineer",
                "company": "Tech Corp",
                "start_date": "2020-01",
                "end_date": "Present",
                "bullets": [{"text": "Led team of 5 engineers"}],
            }
        ]
        generator._add_experience(mock_doc, experience)

    @patch("cli.generators.docx_generator.Document")
    def test_add_experience_empty(self, mock_document, sample_yaml_file):
        """Test adding empty experience."""
        from cli.generators.docx_generator import DocxGenerator

        mock_doc = MagicMock()
        mock_document.return_value = mock_doc

        generator = DocxGenerator(yaml_path=sample_yaml_file)

        generator._add_experience(mock_doc, None)
        generator._add_experience(mock_doc, [])

    @patch("cli.generators.docx_generator.Document")
    def test_add_education(self, mock_document, sample_yaml_file):
        """Test adding education section."""
        from cli.generators.docx_generator import DocxGenerator

        mock_doc = MagicMock()
        mock_document.return_value = mock_doc

        generator = DocxGenerator(yaml_path=sample_yaml_file)

        education = [
            {
                "institution": "MIT",
                "degree": "Bachelor of Science",
                "field": "Computer Science",
                "graduation_date": "2010",
            }
        ]
        generator._add_education(mock_doc, education)

    @patch("cli.generators.docx_generator.Document")
    def test_add_skills(self, mock_document, sample_yaml_file):
        """Test adding skills section."""
        from cli.generators.docx_generator import DocxGenerator

        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        mock_doc.add_paragraph = MagicMock(return_value=MagicMock())

        generator = DocxGenerator(yaml_path=sample_yaml_file)

        skills = {
            "programming": ["Python", "Java", "Go"],
            "frameworks": ["FastAPI", "Django"],
        }
        generator._add_skills(mock_doc, skills)

    @patch("cli.generators.docx_generator.Document")
    def test_add_skills_with_levels(self, mock_document, sample_yaml_file):
        """Test adding skills with proficiency levels."""
        from cli.generators.docx_generator import DocxGenerator

        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        mock_doc.add_paragraph = MagicMock(return_value=MagicMock())

        generator = DocxGenerator(yaml_path=sample_yaml_file)

        skills = {
            "programming": [
                {"name": "Python", "level": "Expert"},
                {"name": "Java", "level": "Intermediate"},
            ]
        }
        generator._add_skills(mock_doc, skills)

    @patch("cli.generators.docx_generator.Document")
    def test_add_publications(self, mock_document, sample_yaml_file):
        """Test adding publications section."""
        from cli.generators.docx_generator import DocxGenerator

        mock_doc = MagicMock()
        mock_document.return_value = mock_doc

        generator = DocxGenerator(yaml_path=sample_yaml_file)

        publications = [
            {
                "title": "Research Paper",
                "authors": "John Doe",
                "year": "2020",
                "journal": "IEEE",
            }
        ]
        generator._add_publications(mock_doc, publications)

    @patch("cli.generators.docx_generator.Document")
    def test_add_certifications(self, mock_document, sample_yaml_file):
        """Test adding certifications section."""
        from cli.generators.docx_generator import DocxGenerator

        mock_doc = MagicMock()
        mock_document.return_value = mock_doc

        generator = DocxGenerator(yaml_path=sample_yaml_file)

        certifications = [
            {"name": "AWS Solutions Architect", "issuer": "Amazon", "license_number": "12345"}
        ]
        generator._add_certifications(mock_doc, certifications)


class TestDocxGeneratorSectionHeading:
    """Tests for _add_section_heading method."""

    @patch("cli.generators.docx_generator.Document")
    def test_add_section_heading(self, mock_document, sample_yaml_file):
        """Test adding section heading."""
        from cli.generators.docx_generator import DocxGenerator

        mock_doc = MagicMock()
        mock_doc.add_paragraph = MagicMock(return_value=MagicMock())
        mock_run = MagicMock()
        mock_doc.add_paragraph.return_value.add_run = MagicMock(return_value=mock_run)

        generator = DocxGenerator(yaml_path=sample_yaml_file)
        generator._add_section_heading(mock_doc, "Experience")

        mock_doc.add_paragraph.assert_called_once()
