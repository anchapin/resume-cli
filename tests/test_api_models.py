"""Unit tests for API models."""

import pytest

from api.models import ResumeRequest, TailorRequest


class TestResumeRequest:
    """Test ResumeRequest model."""

    def test_resume_request_initialization(self):
        """Test ResumeRequest initialization."""
        request = ResumeRequest(resume_data={"name": "John"}, variant="backend")

        assert request.resume_data == {"name": "John"}
        assert request.variant == "backend"

    def test_resume_request_default_variant(self):
        """Test ResumeRequest uses default variant."""
        request = ResumeRequest(resume_data={"name": "John"})

        assert request.variant == "base"

    def test_resume_request_validation_success(self):
        """Test ResumeRequest validation succeeds with required fields."""
        request = ResumeRequest(resume_data={"name": "John"})

        # Pydantic validation passes
        assert request.resume_data == {"name": "John"}

    def test_resume_request_complex_data(self):
        """Test ResumeRequest handles complex resume data."""
        complex_data = {
            "meta": {"version": "1.0"},
            "contact": {"name": "John Doe", "email": "john@example.com", "phone": "+1-555-1234"},
            "experience": [
                {"company": "Acme", "title": "Engineer", "bullets": [{"text": "Did work"}]}
            ],
        }

        request = ResumeRequest(resume_data=complex_data)

        assert request.resume_data == complex_data

    def test_resume_request_empty_resume_data(self):
        """Test ResumeRequest handles empty resume_data dict."""
        request = ResumeRequest(resume_data={})

        assert request.resume_data == {}


class TestTailorRequest:
    """Test TailorRequest model."""

    def test_tailor_request_initialization(self):
        """Test TailorRequest initialization."""
        request = TailorRequest(
            resume_data={"name": "John"}, job_description="Senior Python Engineer needed"
        )

        assert request.resume_data == {"name": "John"}
        assert request.job_description == "Senior Python Engineer needed"

    def test_tailor_request_short_description(self):
        """Test TailorRequest with short job description."""
        request = TailorRequest(resume_data={"name": "Jane"}, job_description="Engineer")

        assert request.job_description == "Engineer"

    def test_tailor_request_long_description(self):
        """Test TailorRequest with long job description."""
        long_desc = "We are looking for a Senior Software Engineer with 10+ years of experience in distributed systems, microservices architecture, cloud-native applications using Go, Python, or Rust. Experience with Kubernetes, Docker, and CI/CD pipelines is required. You will be working on a team of 5-7 engineers building next-generation platform for enterprise clients."

        request = TailorRequest(resume_data={"name": "Bob"}, job_description=long_desc)

        assert request.job_description == long_desc

    def test_tailor_request_special_characters(self):
        """Test TailorRequest handles special characters."""
        request = TailorRequest(
            resume_data={"name": "Alice"},
            job_description="Engineer needed - must know Python, Java & C++ / C#",
        )

        assert request.job_description == "Engineer needed - must know Python, Java & C++ / C#"

    def test_tailor_request_multiline_description(self):
        """Test TailorRequest handles multiline job description."""
        multiline_desc = """Senior Software Engineer

Requirements:
- 5+ years Python experience
- Knowledge of Django/Flask
- AWS/GCP experience
- Bachelor's degree in CS or equivalent

Responsibilities:
- Design and implement backend services
- Collaborate with frontend team
- Optimize database performance
"""

        request = TailorRequest(resume_data={"name": "Charlie"}, job_description=multiline_desc)

        assert request.job_description == multiline_desc
