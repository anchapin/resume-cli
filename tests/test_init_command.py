"""Unit tests for init command."""

from pathlib import Path

import yaml

from cli.commands.init import (
    _add_default_variants,
    _parse_base_resume,
    _parse_revised_resume,
    init_from_existing,
)


class TestInitFromExisting:
    """Test init_from_existing function."""

    def test_init_from_existing_creates_yaml(self, temp_dir: Path):
        """Test init_from_existing creates resume.yaml."""
        # Create mock resume files
        base_resume = temp_dir / "base_resume.txt"
        base_resume.write_text(
            "John Doe, P.E.\n555-123-4567 | john@example.com\n\n"
            "PROFESSIONAL SUMMARY\nExperienced engineer.\n\n"
            "TECHNICAL SKILLS\n• Python: Django, Flask"
        )

        revised_resume = temp_dir / "REVISED.md"
        revised_resume.write_text("John Doe, San Francisco, CA 94102\nhttps://github.com/johndoe")

        output_path = temp_dir / "resume.yaml"

        result = init_from_existing(
            base_resume_path=base_resume,
            revised_resume_path=revised_resume,
            output_path=output_path,
        )

        assert output_path.exists()
        assert result == output_path

    def test_init_from_existing_with_defaults(self, temp_dir: Path):
        """Test init_from_existing uses default paths when None."""
        # Create minimal content
        base_resume = temp_dir / "base_resume.txt"
        base_resume.write_text("John Doe\n555-123-4567 | john@example.com")

        output_path = temp_dir / "resume.yaml"

        init_from_existing(
            base_resume_path=base_resume,
            output_path=output_path,
        )

        assert output_path.exists()

    def test_init_from_existing_no_files(self, temp_dir: Path):
        """Test init_from_existing works with no files."""
        output_path = temp_dir / "resume.yaml"

        init_from_existing(
            base_resume_path=None,
            revised_resume_path=None,
            output_path=output_path,
        )

        assert output_path.exists()
        # Check basic structure
        with open(output_path) as f:
            data = yaml.safe_load(f)

        assert "meta" in data
        assert "contact" in data
        assert "experience" in data


class TestParseBaseResume:
    """Test _parse_base_resume function."""

    def test_parse_base_resume_basic(self, temp_dir: Path):
        """Test parsing basic resume format."""
        resume_file = temp_dir / "resume.txt"
        resume_file.write_text(
            "John Doe\n"
            "555-123-4567 | john@example.com\n"
            "\n"
            "PROFESSIONAL SUMMARY\n"
            "Experienced software engineer.\n"
            "\n"
            "TECHNICAL SKILLS\n"
            "• Python: Django, Flask\n"
            "• JavaScript: React, Node.js\n"
            "\n"
            "EXPERIENCE\n"
            "Tech Corp | 2020 – Present\n"
            "• Built scalable APIs\n"
            "• Led team of engineers\n"
            "\n"
            "EDUCATION\n"
            "Bachelor of Science | University | 2015\n"
        )

        empty_data = {
            "contact": {},
            "professional_summary": {"base": "", "variants": {}},
            "skills": {},
            "experience": [],
            "education": [],
            "variants": {},
        }

        data = empty_data.copy()

        _parse_base_resume(resume_file, data)

        assert data["contact"]["name"] == "John Doe"
        assert data["contact"]["phone"] == "555-123-4567"
        assert data["contact"]["email"] == "john@example.com"
        assert data["professional_summary"]["base"] == "Experienced software engineer."
        assert "python" in data["skills"]
        assert len(data["experience"]) == 1
        assert data["experience"][0]["company"] == "Tech Corp"
        assert len(data["education"]) == 1

    def test_parse_base_resume_with_credentials(self, temp_dir: Path):
        """Test parsing resume with credentials."""
        resume_file = temp_dir / "resume.txt"
        resume_file.write_text("John Doe, PhD\n555-123-4567 | john@example.com")

        empty_data = {
            "contact": {},
            "professional_summary": {"base": "", "variants": {}},
            "skills": {},
            "experience": [],
            "education": [],
            "variants": {},
        }

        _parse_base_resume(resume_file, empty_data)

        assert empty_data["contact"]["name"] == "John Doe"
        assert empty_data["contact"]["credentials"] == ["PhD"]

    def test_parse_base_resume_skills_with_bullets(self, temp_dir: Path):
        """Test parsing skills with bullet format."""
        resume_file = temp_dir / "resume.txt"
        resume_file.write_text(
            "John Doe\n"
            "555-123-4567 | john@example.com\n"
            "\n"
            "TECHNICAL SKILLS\n"
            "• programming: Python, JavaScript\n"
            "• cloud: AWS, GCP"
        )

        empty_data = {
            "contact": {},
            "professional_summary": {"base": "", "variants": {}},
            "skills": {},
            "experience": [],
            "education": [],
            "variants": {},
        }

        _parse_base_resume(resume_file, empty_data)

        assert "programming" in empty_data["skills"]
        assert "cloud" in empty_data["skills"]
        assert "Python" in empty_data["skills"]["programming"]
        assert "AWS" in empty_data["skills"]["cloud"]

    def test_parse_base_resume_experience_bullets_with_skills(self, temp_dir: Path):
        """Test parsing experience bullets with skill labels."""
        resume_file = temp_dir / "resume.txt"
        resume_file.write_text(
            "John Doe\n"
            "555-123-4567 | john@example.com\n"
            "\n"
            "EXPERIENCE\n"
            "Tech Corp | 2020 – 2023\n"
            "• Python: Built scalable APIs\n"
            "• Leadership: Led team of 5\n"
        )

        empty_data = {
            "contact": {},
            "professional_summary": {"base": "", "variants": {}},
            "skills": {},
            "experience": [],
            "education": [],
            "variants": {},
        }

        _parse_base_resume(resume_file, empty_data)

        assert len(empty_data["experience"]) == 1
        assert len(empty_data["experience"][0]["bullets"]) == 2
        assert empty_data["experience"][0]["bullets"][0]["text"] == "Built scalable APIs"
        assert empty_data["experience"][0]["bullets"][0]["skills"] == ["Python"]

    def test_parse_base_resume_past_job(self, temp_dir: Path):
        """Test parsing past job with end date."""
        resume_file = temp_dir / "resume.txt"
        resume_file.write_text(
            "John Doe\n"
            "555-123-4567 | john@example.com\n"
            "\n"
            "EXPERIENCE\n"
            "Tech Corp | 2018 – 2020\n"
            "• Did important work\n"
        )

        empty_data = {
            "contact": {},
            "professional_summary": {"base": "", "variants": {}},
            "skills": {},
            "experience": [],
            "education": [],
            "variants": {},
        }

        _parse_base_resume(resume_file, empty_data)

        assert empty_data["experience"][0]["start_date"] == "2018-01"
        assert empty_data["experience"][0]["end_date"] == "2020-01"

    def test_parse_base_resume_present_job(self, temp_dir: Path):
        """Test parsing present job."""
        resume_file = temp_dir / "resume.txt"
        resume_file.write_text(
            "John Doe\n"
            "555-123-4567 | john@example.com\n"
            "\n"
            "EXPERIENCE\n"
            "Tech Corp | 2020 – Present\n"
            "• Current work\n"
        )

        empty_data = {
            "contact": {},
            "professional_summary": {"base": "", "variants": {}},
            "skills": {},
            "experience": [],
            "education": [],
            "variants": {},
        }

        _parse_base_resume(resume_file, empty_data)

        assert empty_data["experience"][0]["end_date"] is None


class TestParseRevisedResume:
    """Test _parse_revised_resume function."""

    def test_parse_revised_resume_location(self, temp_dir: Path):
        """Test parsing location from revised resume."""
        revised_file = temp_dir / "revised.md"
        revised_file.write_text("John Doe\nSan Francisco, CA 94102")

        data = {"contact": {}}

        _parse_revised_resume(revised_file, data)

        assert data["contact"]["location"]["city"] == "San Francisco"
        assert data["contact"]["location"]["state"] == "CA"
        assert data["contact"]["location"]["zip"] == "94102"

    def test_parse_revised_resume_github(self, temp_dir: Path):
        """Test parsing GitHub URL from revised resume."""
        revised_file = temp_dir / "revised.md"
        revised_file.write_text("John Doe\nhttps://github.com/johndoe")

        data = {"contact": {}}

        _parse_revised_resume(revised_file, data)

        assert data["contact"]["urls"]["github"] == "https://github.com/johndoe"

    def test_parse_revised_resume_linkedin(self, temp_dir: Path):
        """Test parsing LinkedIn URL from revised resume."""
        revised_file = temp_dir / "revised.md"
        revised_file.write_text("John Doe\nhttps://linkedin.com/in/johndoe")

        data = {"contact": {}}

        _parse_revised_resume(revised_file, data)

        assert data["contact"]["urls"]["linkedin"] == "https://linkedin.com/in/johndoe"


class TestAddDefaultVariants:
    """Test _add_default_variants function."""

    def test_add_default_variants(self):
        """Test adding default variants."""
        data = {"skills": {"programming": ["Python"], "cloud": ["AWS"]}, "variants": {}}

        _add_default_variants(data)

        assert "v1.0.0-base" in data["variants"]
        assert "v1.1.0-backend" in data["variants"]
        assert "v1.2.0-ml_ai" in data["variants"]
        assert "v1.3.0-fullstack" in data["variants"]

    def test_add_default_variants_includes_skill_sections(self):
        """Test default variants include skill sections."""
        data = {"skills": {"programming": ["Python"], "cloud": ["AWS"]}, "variants": {}}

        _add_default_variants(data)

        assert "skill_sections" in data["variants"]["v1.0.0-base"]
        assert "programming" in data["variants"]["v1.0.0-base"]["skill_sections"]

    def test_add_default_variants_backend_focus(self):
        """Test backend variant has backend-specific config."""
        data = {
            "skills": {"programming": ["Python"], "cloud": ["AWS"]},
            "variants": {},
        }

        _add_default_variants(data)

        backend = data["variants"]["v1.1.0-backend"]
        assert "backend" in str(backend.get("emphasize_keywords", [])).lower()

    def test_add_default_variants_ml_ai_focus(self):
        """Test ML/AI variant has ML-specific config."""
        data = {
            "skills": {"programming": ["Python"], "ai_ml": ["TensorFlow"]},
            "variants": {},
        }

        _add_default_variants(data)

        ml_ai = data["variants"]["v1.2.0-ml_ai"]
        keywords = ml_ai.get("emphasize_keywords", [])
        assert "ai" in str(keywords).lower() or "ml" in str(keywords).lower()
