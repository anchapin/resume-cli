"""Tests for TXT resume generator."""



class TestTxtGeneratorInitialization:
    """Tests for TxtGenerator initialization."""

    def test_init_with_yaml_path(self, sample_yaml_file):
        """Test initialization with yaml_path."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)
        assert generator.yaml_handler is not None
        assert generator.config is not None

    def test_init_with_config(self, sample_yaml_file):
        """Test initialization with config."""
        from cli.generators.txt_generator import TxtGenerator
        from cli.utils.config import Config

        config = Config()
        generator = TxtGenerator(yaml_path=sample_yaml_file, config=config)
        assert generator.config is config

    def test_init_without_params(self):
        """Test initialization without parameters."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator()
        assert generator.yaml_handler is not None
        assert generator.config is not None

    def test_separator_constants(self):
        """Test separator constants are defined."""
        from cli.generators.txt_generator import TxtGenerator

        assert TxtGenerator.SECTION_SEPARATOR == "=" * 80
        assert TxtGenerator.SUBSECTION_SEPARATOR == "-" * 40


class TestTxtGeneratorGenerate:
    """Tests for TxtGenerator.generate method."""

    def test_generate_basic(self, sample_yaml_file):
        """Test basic generate call."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)
        result = generator.generate(variant="v1.0.0-base")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_with_output_path(self, sample_yaml_file, temp_dir):
        """Test generate with output path."""
        from cli.generators.txt_generator import TxtGenerator

        output_path = temp_dir / "resume.txt"
        generator = TxtGenerator(yaml_path=sample_yaml_file)
        result = generator.generate(variant="v1.0.0-base", output_path=output_path)

        assert isinstance(result, str)
        assert output_path.exists()
        assert output_path.read_text() == result

    def test_generate_backend_variant(self, sample_yaml_file):
        """Test generate with backend variant."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)
        result = generator.generate(variant="v1.1.0-backend")

        assert isinstance(result, str)
        assert "PROFESSIONAL SUMMARY" in result

    def test_generate_ml_ai_variant(self, sample_yaml_file):
        """Test generate with ML/AI variant."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)
        result = generator.generate(variant="v1.2.0-ml_ai")

        assert isinstance(result, str)

    def test_generate_with_enhanced_context(self, sample_yaml_file):
        """Test generate with enhanced context."""
        from cli.generators.txt_generator import TxtGenerator

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

        generator = TxtGenerator(yaml_path=sample_yaml_file)
        result = generator.generate(variant="v1.0.0-base", enhanced_context=enhanced_context)

        assert isinstance(result, str)
        assert "Enhanced summary with AI improvements" in result


class TestTxtGeneratorBuildHeader:
    """Tests for _build_header method."""

    def test_build_header_with_name(self, sample_yaml_file):
        """Test building header with name."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        contact = {"name": "John Doe", "email": "john@example.com", "phone": "555-1234"}
        lines = generator._build_header(contact)

        assert "John Doe" in lines
        assert "john@example.com" in " ".join(lines)

    def test_build_header_with_location(self, sample_yaml_file):
        """Test building header with location."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        contact = {
            "name": "John Doe",
            "location": {"city": "Boston", "state": "MA"},
            "email": "john@example.com",
        }
        lines = generator._build_header(contact)

        assert "Boston" in " ".join(lines)
        assert "MA" in " ".join(lines)

    def test_build_header_with_urls(self, sample_yaml_file):
        """Test building header with URLs."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        contact = {
            "name": "John Doe",
            "urls": {
                "github": "https://github.com/johndoe",
                "linkedin": "https://linkedin.com/in/johndoe",
            },
        }
        lines = generator._build_header(contact)

        assert "https://github.com/johndoe" in " ".join(lines)
        assert "https://linkedin.com/in/johndoe" in " ".join(lines)

    def test_build_header_with_credentials(self, sample_yaml_file):
        """Test building header with credentials."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        contact = {
            "name": "John Doe",
            "credentials": ["MBA", "PMP"],
        }
        lines = generator._build_header(contact)

        assert "John Doe" in lines
        assert "MBA" in " ".join(lines)
        assert "PMP" in " ".join(lines)

    def test_build_header_includes_separator(self, sample_yaml_file):
        """Test that header includes section separator."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        contact = {"name": "John Doe"}
        lines = generator._build_header(contact)

        assert "=" * 80 in lines


class TestTxtGeneratorBuildSections:
    """Tests for section building methods."""

    def test_build_summary(self, sample_yaml_file):
        """Test building summary section."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        summary = {"content": "Experienced professional with 10+ years..."}
        lines = generator._build_summary(summary)

        assert "PROFESSIONAL SUMMARY" in lines
        assert "Experienced professional with 10+ years..." in " ".join(lines)

    def test_build_summary_empty(self, sample_yaml_file):
        """Test building empty summary."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        lines_none = generator._build_summary(None)
        lines_empty = generator._build_summary({})

        assert lines_none == []
        assert lines_empty == []

    def test_build_projects(self, sample_yaml_file):
        """Test building projects section."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        projects = {
            "ai_ml": [
                {
                    "name": "Test Project",
                    "description": "A test project",
                    "url": "https://github.com/test",
                }
            ]
        }
        lines = generator._build_projects(projects)

        assert "PROJECTS" in lines
        assert "AI/ML" in " ".join(lines)
        assert "Test Project" in " ".join(lines)

    def test_build_projects_empty(self, sample_yaml_file):
        """Test building empty projects."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        lines_none = generator._build_projects(None)
        lines_empty = generator._build_projects({})

        assert lines_none == []
        assert lines_empty == []

    def test_build_experience(self, sample_yaml_file):
        """Test building experience section."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        experience = [
            {
                "title": "Senior Engineer",
                "company": "Tech Corp",
                "start_date": "2020-01",
                "end_date": "Present",
                "bullets": [{"text": "Led team of 5 engineers"}],
            }
        ]
        lines = generator._build_experience(experience)

        assert "PROFESSIONAL EXPERIENCE" in lines
        assert "Senior Engineer" in " ".join(lines)
        assert "Tech Corp" in " ".join(lines)
        assert "Led team of 5 engineers" in " ".join(lines)

    def test_build_experience_empty(self, sample_yaml_file):
        """Test building empty experience."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        lines_none = generator._build_experience(None)
        lines_empty = generator._build_experience([])

        assert lines_none == []
        assert lines_empty == []

    def test_build_experience_current_job(self, sample_yaml_file):
        """Test building experience with current job (no end date)."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        experience = [
            {
                "title": "Staff Engineer",
                "company": "Current Corp",
                "start_date": "2024-01",
                "end_date": None,
                "bullets": [],
            }
        ]
        lines = generator._build_experience(experience)

        assert "Present" in " ".join(lines)

    def test_build_education(self, sample_yaml_file):
        """Test building education section."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        education = [
            {
                "institution": "MIT",
                "degree": "Bachelor of Science",
                "field": "Computer Science",
                "graduation_date": "2010",
            }
        ]
        lines = generator._build_education(education)

        assert "EDUCATION" in lines
        assert "MIT" in " ".join(lines)
        assert "Computer Science" in " ".join(lines)

    def test_build_skills(self, sample_yaml_file):
        """Test building skills section."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        skills = {
            "programming": ["Python", "Java", "Go"],
            "frameworks": ["FastAPI", "Django"],
        }
        lines = generator._build_skills(skills)

        assert "SKILLS" in lines
        assert "Programming:" in " ".join(lines)
        assert "Python" in " ".join(lines)
        assert "Java" in " ".join(lines)

    def test_build_skills_with_levels(self, sample_yaml_file):
        """Test building skills with proficiency levels."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        skills = {
            "programming": [
                {"name": "Python", "level": "Expert"},
                {"name": "Java", "level": "Intermediate"},
            ]
        }
        lines = generator._build_skills(skills)

        assert "Python (Expert)" in " ".join(lines)
        assert "Java (Intermediate)" in " ".join(lines)

    def test_build_publications(self, sample_yaml_file):
        """Test building publications section."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        publications = [
            {
                "title": "Research Paper",
                "authors": "John Doe",
                "year": "2020",
                "journal": "IEEE",
            }
        ]
        lines = generator._build_publications(publications)

        assert "PUBLICATIONS" in lines
        assert "Research Paper" in " ".join(lines)
        assert "John Doe" in " ".join(lines)

    def test_build_certifications(self, sample_yaml_file):
        """Test building certifications section."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        certifications = [
            {"name": "AWS Solutions Architect", "issuer": "Amazon", "license_number": "12345"}
        ]
        lines = generator._build_certifications(certifications)

        assert "CERTIFICATIONS" in lines
        assert "AWS Solutions Architect" in " ".join(lines)
        assert "Amazon" in " ".join(lines)


class TestTxtGeneratorWrapText:
    """Tests for _wrap_text method."""

    def test_wrap_text_basic(self, sample_yaml_file):
        """Test basic text wrapping."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        text = "This is a short sentence."
        lines = generator._wrap_text(text, width=80)

        assert len(lines) == 1
        assert lines[0] == "This is a short sentence."

    def test_wrap_text_long(self, sample_yaml_file):
        """Test wrapping long text."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        text = "This is a very long sentence that should be wrapped to multiple lines because it exceeds the specified width limit."
        lines = generator._wrap_text(text, width=40)

        assert len(lines) > 1
        for line in lines:
            assert len(line) <= 40

    def test_wrap_text_with_indent(self, sample_yaml_file):
        """Test wrapping text with indent."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        text = "This is a long sentence that should be wrapped with indentation on each line."
        lines = generator._wrap_text(text, width=40, indent="  ")

        assert len(lines) > 1
        for line in lines:
            assert line.startswith("  ")
            assert len(line) <= 40

    def test_wrap_text_empty(self, sample_yaml_file):
        """Test wrapping empty text."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        lines = generator._wrap_text("", width=80)

        assert lines == []


class TestTxtGeneratorAsciiSafe:
    """Tests for ASCII-safe output."""

    def test_output_is_ascii_safe(self, sample_yaml_file):
        """Test that generated output uses ASCII-safe characters."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)
        result = generator.generate(variant="v1.0.0-base")

        # Check that all characters are ASCII
        for char in result:
            assert ord(char) < 128, f"Non-ASCII character found: {char}"

    def test_no_unicode_characters(self, sample_yaml_file):
        """Test that no Unicode special characters are used."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        contact = {
            "name": "John Doe",
            "location": {"city": "San Francisco", "state": "CA"},
            "email": "john@example.com",
        }
        lines = generator._build_header(contact)
        content = "\n".join(lines)

        # Check no Unicode dashes or other special chars
        assert "\u2014" not in content  # em dash
        assert "\u2013" not in content  # en dash
        assert "\u2022" not in content  # bullet


class TestTxtGeneratorSectionHeadings:
    """Tests for section heading formatting."""

    def test_section_heading_uppercase(self, sample_yaml_file):
        """Test that section headings are uppercase."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)

        lines = generator._build_section_heading("Professional Summary")

        assert "PROFESSIONAL SUMMARY" in lines

    def test_all_expected_sections_present(self, sample_yaml_file):
        """Test that all expected sections are present in output."""
        from cli.generators.txt_generator import TxtGenerator

        generator = TxtGenerator(yaml_path=sample_yaml_file)
        result = generator.generate(variant="v1.0.0-base")

        # Check for expected section headings
        assert "PROFESSIONAL SUMMARY" in result
        assert "PROJECTS" in result or "PROFESSIONAL EXPERIENCE" in result
        assert "SKILLS" in result
