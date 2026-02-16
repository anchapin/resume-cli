"""Tests for LinkedIn integration."""

import json
import tempfile
from pathlib import Path

import pytest

from cli.integrations.linkedin import LinkedInSync


class MockConfig:
    """Mock config object for testing."""

    def get(self, key, default=None):
        return default


@pytest.fixture
def mock_config():
    """Return a mock config object."""
    return MockConfig()


@pytest.fixture
def sample_linkedin_data():
    """Sample LinkedIn export data."""
    return {
        "profile": {
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-0123",
            "location": {"city": "San Francisco", "region": "California"},
            "website": "https://johndoe.dev",
            "linkedinUrl": "https://linkedin.com/in/johndoe",
            "headline": "Senior Software Engineer",
            "summary": "Experienced software engineer with 10+ years of experience.",
        },
        "skills": [
            {"name": "Python"},
            {"name": "JavaScript"},
            {"name": "Docker"},
            {"name": "Kubernetes"},
            {"name": "AWS"},
            {"name": "PostgreSQL"},
        ],
        "experience": [
            {
                "company": "Tech Corp",
                "title": "Senior Software Engineer",
                "startDate": "2020-01",
                "endDate": "2023-12",
                "location": "San Francisco, CA",
                "description": "• Built microservices using Python and FastAPI\n• Reduced API latency by 40%\n• Led team of 5 engineers",
            },
            {
                "company": "Startup Inc",
                "title": "Software Engineer",
                "startDate": "2018-06",
                "endDate": "2019-12",
                "location": "New York, NY",
                "description": "Developed React frontend applications",
            },
        ],
        "education": [
            {
                "school": "MIT",
                "degree": "Master of Science",
                "fieldOfStudy": "Computer Science",
                "startDate": "2016-09",
                "endDate": "2018-05",
                "schoolLocation": "Cambridge, MA",
            },
            {
                "school": "State University",
                "degree": "Bachelor of Science",
                "fieldOfStudy": "Computer Science",
                "endDate": "2016-05",
            },
        ],
        "certifications": [
            {
                "name": "AWS Certified Solutions Architect",
                "authority": "Amazon Web Services",
                "startDate": "2021-03",
                "url": "https://aws.amazon.com/certification/",
            }
        ],
    }


@pytest.fixture
def sample_resume_data():
    """Sample resume.yaml data."""
    return {
        "meta": {"version": "2.0.0", "last_updated": "2024-01-01", "author": "John Doe"},
        "contact": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-0123",
            "location": {"city": "San Francisco", "state": "California"},
        },
        "professional_summary": {
            "base": "Software engineer with experience in Python and JavaScript.",
            "variants": {},
        },
        "skills": {"languages": ["Python", "JavaScript"], "frameworks": ["Django", "React"]},
        "experience": [
            {
                "company": "Tech Corp",
                "title": "Senior Software Engineer",
                "start_date": "2020-01",
                "end_date": "2023-12",
                "location": "San Francisco, CA",
                "bullets": [{"text": "Built microservices", "skills": [], "emphasize_for": []}],
            }
        ],
        "education": [
            {
                "institution": "MIT",
                "degree": "Master of Science",
                "graduation_date": "2018-05",
                "field": "Computer Science",
            }
        ],
        "certifications": [],
        "projects": {},
        "variants": {
            "v1.0.0-base": {
                "description": "Base variant",
                "skill_sections": ["languages", "frameworks"],
            }
        },
    }


class TestLinkedInSync:
    """Test cases for LinkedInSync class."""

    def test_init(self, mock_config):
        """Test LinkedInSync initialization."""
        sync = LinkedInSync(mock_config)
        assert sync.config == mock_config
        assert sync.linkedin_config is not None

    def test_import_from_url_raises_error(self, mock_config):
        """Test that import_from_url raises NotImplementedError."""
        sync = LinkedInSync(mock_config)
        with pytest.raises(
            NotImplementedError, match="Direct LinkedIn URL import is not supported"
        ):
            sync.import_from_url("https://linkedin.com/in/username")

    def test_import_from_json_file_not_found(self, mock_config):
        """Test import_from_json with non-existent file."""
        sync = LinkedInSync(mock_config)
        with pytest.raises(FileNotFoundError, match="LinkedIn data file not found"):
            sync.import_from_json(Path("/nonexistent/file.json"))

    def test_extract_contact(self, mock_config, sample_linkedin_data):
        """Test contact extraction."""
        sync = LinkedInSync(mock_config)
        contact = sync._extract_contact(sample_linkedin_data)

        assert contact["name"] == "John Doe"
        assert contact["email"] == "john.doe@example.com"
        assert contact["phone"] == "+1-555-0123"
        assert contact["location"]["city"] == "San Francisco"
        assert contact["location"]["state"] == "California"

    def test_extract_summary(self, mock_config, sample_linkedin_data):
        """Test summary extraction."""
        sync = LinkedInSync(mock_config)
        summary = sync._extract_summary(sample_linkedin_data)

        assert summary["base"] == "Experienced software engineer with 10+ years of experience."
        assert "variants" in summary

    def test_extract_skills(self, mock_config, sample_linkedin_data):
        """Test skills extraction and categorization."""
        sync = LinkedInSync(mock_config)
        skills = sync._extract_skills(sample_linkedin_data)

        # Check that skills are categorized
        assert "languages" in skills
        assert "cloud_platforms" in skills
        assert "databases" in skills

        # Check specific skill placement
        assert "Python" in skills["languages"]
        assert "JavaScript" in skills["languages"]
        assert "AWS" in skills["cloud_platforms"]
        assert "PostgreSQL" in skills["databases"]

    def test_extract_experience(self, mock_config, sample_linkedin_data):
        """Test experience extraction."""
        sync = LinkedInSync(mock_config)
        experience = sync._extract_experience(sample_linkedin_data)

        assert len(experience) == 2
        assert experience[0]["company"] == "Tech Corp"
        assert experience[0]["title"] == "Senior Software Engineer"
        assert experience[0]["start_date"] == "2020-01"
        assert experience[0]["end_date"] == "2023-12"
        assert len(experience[0]["bullets"]) > 0

    def test_extract_education(self, mock_config, sample_linkedin_data):
        """Test education extraction."""
        sync = LinkedInSync(mock_config)
        education = sync._extract_education(sample_linkedin_data)

        assert len(education) == 2
        assert education[0]["institution"] == "MIT"
        assert education[0]["degree"] == "Master of Science"
        assert education[0]["field"] == "Computer Science"
        assert education[0]["graduation_date"] == "2018-05"

    def test_extract_certifications(self, mock_config, sample_linkedin_data):
        """Test certifications extraction."""
        sync = LinkedInSync(mock_config)
        certifications = sync._extract_certifications(sample_linkedin_data)

        assert len(certifications) == 1
        assert certifications[0]["name"] == "AWS Certified Solutions Architect"
        assert certifications[0]["issuer"] == "Amazon Web Services"

    def test_parse_linkedin_date(self, mock_config):
        """Test date parsing."""
        sync = LinkedInSync(mock_config)

        # Test various formats
        assert sync._parse_linkedin_date("2020-01-15") == "2020-01"
        assert sync._parse_linkedin_date("2020-01") == "2020-01"
        assert sync._parse_linkedin_date("January 2020") == "2020-01"
        assert sync._parse_linkedin_date("Jan 2020") == "2020-01"
        assert sync._parse_linkedin_date("2020") == "2020-01"
        assert sync._parse_linkedin_date("01/2020") == "2020-01"
        assert sync._parse_linkedin_date("01/15/2020") == "2020-01"
        assert sync._parse_linkedin_date(None) is None
        assert sync._parse_linkedin_date("") is None

    def test_categorize_skills(self, mock_config):
        """Test skill categorization."""
        sync = LinkedInSync(mock_config)

        skills = [
            "Python",
            "JavaScript",
            "Docker",
            "Kubernetes",
            "AWS",
            "PostgreSQL",
            "Django",
            "React",
            "MongoDB",
            "Redis",
            "Git",
            "Jenkins",
        ]

        categorized = sync._categorize_skills(skills)

        assert "Python" in categorized["languages"]
        assert "JavaScript" in categorized["languages"]
        assert "Django" in categorized["frameworks"]
        assert "React" in categorized["frameworks"]
        assert "Docker" in categorized["tools"]
        assert "Kubernetes" in categorized["tools"]
        assert "AWS" in categorized["cloud_platforms"]
        assert "PostgreSQL" in categorized["databases"]

    def test_parse_description_to_bullets(self, mock_config):
        """Test parsing description to bullets."""
        sync = LinkedInSync(mock_config)

        description = "• Built microservices\n• Reduced API latency\n• Led engineering team"
        bullets = sync._parse_description_to_bullets(description)

        assert len(bullets) == 3
        assert bullets[0]["text"] == "Built microservices"
        assert bullets[1]["text"] == "Reduced API latency"
        assert bullets[2]["text"] == "Led engineering team"

    def test_full_import_workflow(self, mock_config, sample_linkedin_data):
        """Test full import workflow from JSON to resume data."""
        sync = LinkedInSync(mock_config)

        # Write sample data to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_linkedin_data, f)
            temp_path = Path(f.name)

        try:
            # Import
            resume_data = sync.import_from_json(temp_path)

            # Verify structure
            assert "meta" in resume_data
            assert "contact" in resume_data
            assert "professional_summary" in resume_data
            assert "skills" in resume_data
            assert "experience" in resume_data
            assert "education" in resume_data
            assert "certifications" in resume_data
            assert "variants" in resume_data

            # Verify content
            assert resume_data["contact"]["name"] == "John Doe"
            assert len(resume_data["experience"]) == 2
            assert len(resume_data["education"]) == 2
            assert len(resume_data["certifications"]) == 1

        finally:
            temp_path.unlink()

    def test_format_date_range(self, mock_config):
        """Test date range formatting for LinkedIn export."""
        sync = LinkedInSync(mock_config)

        assert sync._format_date_range("2020-01", "2023-12") == "Jan 2020 - Dec 2023"
        assert sync._format_date_range("2020-01", "Present") == "Jan 2020 - Present"
        assert sync._format_date_range("2020-01", None) == "Jan 2020 - Present"

    def test_import_from_csv(self, mock_config):
        """Test importing from CSV file."""
        sync = LinkedInSync(mock_config)

        # Create a temporary CSV file with LinkedIn profile data
        csv_content = """First Name,Last Name,Maiden Name,Address,Birth Date,Headline,Summary,Industry,Zip Code,Geo Location,Twitter Handles,Websites,Instant Messengers
John,Doe,,,Jan 1,"Software Engineer at Tech Corp","Experienced software engineer.","Software Development,12345,"San Francisco, California",,https://johndoe.dev,"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_path = Path(f.name)

        try:
            # Import CSV
            resume_data = sync.import_from_json(temp_path)

            # Verify structure
            assert "meta" in resume_data
            assert "contact" in resume_data
            assert "professional_summary" in resume_data

            # Verify content
            assert resume_data["contact"]["name"] == "John Doe"
            assert resume_data["professional_summary"]["base"] == "Experienced software engineer."
            assert resume_data["professional_summary"]["variants"] == {}

        finally:
            temp_path.unlink()

    def test_import_csv_with_invalid_json_provides_helpful_error(self, mock_config):
        """Test that invalid JSON files give helpful error message about CSV."""
        sync = LinkedInSync(mock_config)

        # Create a temporary file with CSV content but .json extension
        csv_content = "First Name,Last Name\nJohn,Doe"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(csv_content)
            temp_path = Path(f.name)

        try:
            # Import should fail with helpful message
            with pytest.raises(ValueError, match="appears to be in CSV format"):
                sync.import_from_json(temp_path)

        finally:
            temp_path.unlink()


class TestLinkedInMerge:
    """Test cases for merging LinkedIn data with existing resume data."""

    @pytest.fixture
    def imported_resume_data(self, mock_config, sample_linkedin_data):
        """Return properly mapped resume data from LinkedIn export."""
        sync = LinkedInSync(mock_config)
        return sync._map_linkedin_to_resume(sample_linkedin_data)

    def test_merge_contact(self, mock_config, imported_resume_data, sample_resume_data):
        """Test merging contact info."""
        from cli.commands.linkedin import _merge_resume_data

        merged = _merge_resume_data(sample_resume_data, imported_resume_data)

        # Contact should be from imported data
        assert merged["contact"]["name"] == "John Doe"

    def test_merge_skills(self, mock_config, imported_resume_data, sample_resume_data):
        """Test merging skills."""
        from cli.commands.linkedin import _merge_resume_data

        merged = _merge_resume_data(sample_resume_data, imported_resume_data)

        # Skills should be merged without duplicates
        # Both have "languages" category - check Python is there
        assert "languages" in merged["skills"]
        # Imported has categorized skills including tools
        assert "tools" in merged["skills"]
        assert "Docker" in merged["skills"]["tools"]

    def test_merge_experience(self, mock_config, imported_resume_data, sample_resume_data):
        """Test merging experience."""
        from cli.commands.linkedin import _merge_resume_data

        merged = _merge_resume_data(sample_resume_data, imported_resume_data)

        # Should have both existing and imported experience
        assert len(merged["experience"]) >= 2

        # Check for no duplicates
        exp_keys = set()
        for exp in merged["experience"]:
            key = f"{exp.get('company', '')}|{exp.get('title', '')}|{exp.get('start_date', '')}"
            assert key not in exp_keys
            exp_keys.add(key)

    def test_merge_education(self, mock_config, imported_resume_data, sample_resume_data):
        """Test merging education."""
        from cli.commands.linkedin import _merge_resume_data

        merged = _merge_resume_data(sample_resume_data, imported_resume_data)

        # Should have merged education
        assert len(merged["education"]) >= 2

    def test_merge_certifications(self, mock_config, imported_resume_data, sample_resume_data):
        """Test merging certifications."""
        from cli.commands.linkedin import _merge_resume_data

        merged = _merge_resume_data(sample_resume_data, imported_resume_data)

        # Should have imported certification
        assert len(merged["certifications"]) == 1
        assert merged["certifications"][0]["name"] == "AWS Certified Solutions Architect"

    def test_merge_preserves_variants(self, mock_config, imported_resume_data, sample_resume_data):
        """Test that merging preserves existing variants."""
        from cli.commands.linkedin import _merge_resume_data

        merged = _merge_resume_data(sample_resume_data, imported_resume_data)

        # Should preserve existing variants
        assert "v1.0.0-base" in merged["variants"]
        assert merged["variants"]["v1.0.0-base"]["description"] == "Base variant"

    def test_merge_preserves_projects(self, mock_config, imported_resume_data, sample_resume_data):
        """Test that merging preserves existing projects."""
        from cli.commands.linkedin import _merge_resume_data

        merged = _merge_resume_data(sample_resume_data, imported_resume_data)

        # Should preserve projects section
        assert "projects" in merged


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
