"""Shared fixtures and test configuration for pytest."""

from pathlib import Path
from typing import Any, Dict

import pytest
import yaml

from cli.utils.config import Config
from cli.utils.yaml_parser import ResumeYAML


@pytest.fixture(autouse=True)
def setup_ai_environment_variables(monkeypatch):
    """
    Set up required AI environment variables for tests.
    This is an autouse fixture that runs for all tests to ensure
    CoverLetterGenerator and AIGenerator don't fail due to missing API keys.
    """
    # Set dummy API keys for both providers
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for test files."""
    temp_dir = tmp_path / "resume_test"
    temp_dir.mkdir()
    yield temp_dir
    # Cleanup handled by tmp_path fixture


@pytest.fixture
def sample_resume_data() -> Dict[str, Any]:
    """Sample resume data for testing."""
    return {
        "meta": {"version": "2.0.0", "last_updated": "2024-01-15", "author": "Test Author"},
        "contact": {
            "name": "John Doe",
            "phone": "+1-555-123-4567",
            "email": "john.doe@example.com",
            "location": {"city": "San Francisco", "state": "CA", "country": "USA"},
            "urls": {
                "linkedin": "https://linkedin.com/in/johndoe",
                "github": "https://github.com/johndoe",
            },
        },
        "professional_summary": {
            "base": "Experienced software engineer with 10+ years in distributed systems.",
            "variants": {
                "backend": "Backend engineer specializing in scalable APIs and databases.",
                "ml_ai": "ML engineer focused on deep learning and NLP applications.",
                "fullstack": "Full-stack engineer with expertise in React and Python.",
                "devops": "DevOps engineer with expertise in Kubernetes and CI/CD.",
                "leadership": "Engineering leader with 15+ years of team management experience.",
            },
        },
        "skills": {
            "programming": [
                "Python",
                "JavaScript",
                "TypeScript",
                {"name": "Go", "emphasize_for": ["backend", "devops"]},
                "Java",
            ],
            "frameworks": [
                "Django",
                "FastAPI",
                "React",
                {"name": "Kubernetes", "emphasize_for": ["backend", "devops"]},
                "Flask",
            ],
            "databases": [
                "PostgreSQL",
                "MongoDB",
                "Redis",
                {"name": "MySQL", "emphasize_for": ["backend"]},
            ],
            "devops": [
                "Docker",
                "Kubernetes",
                "Git",
                {"name": "Jenkins", "emphasize_for": ["devops"]},
                "GitHub Actions",
            ],
            "cloud": ["AWS", "GCP", "Azure"],
            "ai_ml": [
                "TensorFlow",
                "PyTorch",
                "scikit-learn",
                {"name": "LangChain", "emphasize_for": ["ml_ai"]},
                "Transformers",
            ],
        },
        "experience": [
            {
                "company": "Tech Corp",
                "title": "Senior Software Engineer",
                "start_date": "2020-01",
                "end_date": "2023-12",
                "location": "San Francisco, CA",
                "bullets": [
                    {
                        "text": "Led team of 5 engineers",
                        "skills": ["Leadership"],
                        "emphasize_for": ["leadership"],
                    },
                    {
                        "text": "Built scalable REST API handling 10k+ requests/second",
                        "skills": ["Python", "FastAPI", "Kubernetes"],
                        "emphasize_for": ["backend"],
                    },
                    {
                        "text": "Implemented microservices architecture",
                        "skills": ["Python", "Docker"],
                        "emphasize_for": ["fullstack", "backend"],
                    },
                    {
                        "text": "Deployed ML models to production",
                        "skills": ["TensorFlow", "Kubernetes"],
                        "emphasize_for": ["ml_ai"],
                    },
                    {
                        "text": "Set up CI/CD pipeline",
                        "skills": ["Jenkins", "GitHub Actions"],
                        "emphasize_for": ["devops"],
                    },
                    {"text": "Optimized database queries", "skills": ["PostgreSQL", "Redis"]},
                ],
            },
            {
                "company": "Startup Inc",
                "title": "Software Engineer",
                "start_date": "2018-06",
                "end_date": "2020-01",
                "location": "Remote",
                "bullets": [
                    {
                        "text": "Developed React frontend",
                        "skills": ["React", "JavaScript"],
                        "emphasize_for": ["fullstack"],
                    },
                    {
                        "text": "Built Django backend",
                        "skills": ["Python", "Django"],
                        "emphasize_for": ["backend"],
                    },
                    {
                        "text": "Integrated OpenAI API",
                        "skills": ["Python", "LangChain"],
                        "emphasize_for": ["ml_ai"],
                    },
                    {
                        "text": "Set up AWS infrastructure",
                        "skills": ["AWS", "Docker"],
                        "emphasize_for": ["devops"],
                    },
                ],
            },
            {
                "company": "Current Company",
                "title": "Staff Engineer",
                "start_date": "2024-01",
                "end_date": None,
                "location": "New York, NY",
                "bullets": [
                    {
                        "text": "Leading technical architecture decisions",
                        "skills": ["Leadership"],
                        "emphasize_for": ["leadership"],
                    },
                    {
                        "text": "Mentoring junior engineers",
                        "skills": ["Leadership"],
                        "emphasize_for": ["leadership"],
                    },
                    {
                        "text": "Building real-time analytics system",
                        "skills": ["Python", "Redis", "Kafka"],
                    },
                    {
                        "text": "Deploying models with MLflow",
                        "skills": ["PyTorch", "MLflow"],
                        "emphasize_for": ["ml_ai"],
                    },
                ],
            },
        ],
        "education": [
            {
                "institution": "University of California, Berkeley",
                "degree": "Bachelor of Science",
                "field": "Computer Science",
                "graduation_date": "2015-05",
                "location": "Berkeley, CA",
            },
            {
                "institution": "Stanford University",
                "degree": "Master of Science",
                "field": "Computer Science",
                "graduation_date": "2018-06",
                "location": "Stanford, CA",
            },
        ],
        "publications": [
            {
                "authors": "J. Doe, A. Smith",
                "year": "2020",
                "title": "Distributed Systems at Scale",
                "type": "Journal Article",
                "journal": "IEEE Transactions",
            }
        ],
        "certifications": [
            {"name": "AWS Solutions Architect", "year": "2022"},
            {"name": "Kubernetes Administrator", "year": "2023"},
        ],
        "affiliations": [{"name": "ACM Member", "years": "2015-Present"}],
        "projects": {
            "featured": [
                {
                    "name": "resume-cli",
                    "description": "A CLI tool for generating resumes from YAML",
                    "url": "https://github.com/johndoe/resume-cli",
                    "stars": 150,
                    "language": "Python",
                }
            ],
            "ai_ml": [
                {
                    "name": "ml-pipeline",
                    "description": "Machine learning pipeline for data processing",
                    "url": "https://github.com/johndoe/ml-pipeline",
                    "stars": 75,
                    "language": "Python",
                }
            ],
            "fullstack": [
                {
                    "name": "web-app",
                    "description": "Full-stack web application",
                    "url": "https://github.com/johndoe/web-app",
                    "stars": 50,
                    "language": "TypeScript",
                }
            ],
        },
        "variants": {
            "v1.0.0-base": {
                "description": "Base variant with all content",
                "summary_key": "base",
                "skill_sections": [
                    "programming",
                    "frameworks",
                    "databases",
                    "devops",
                    "cloud",
                    "ai_ml",
                ],
                "max_bullets_per_job": 4,
                "emphasize_keywords": [],
            },
            "v1.1.0-backend": {
                "description": "Backend-focused variant",
                "summary_key": "backend",
                "skill_sections": ["programming", "frameworks", "databases", "devops"],
                "max_bullets_per_job": 4,
                "emphasize_keywords": ["api", "backend", "database", "scalable"],
            },
            "v1.2.0-ml_ai": {
                "description": "ML/AI-focused variant",
                "summary_key": "ml_ai",
                "skill_sections": ["programming", "ai_ml", "frameworks", "databases"],
                "max_bullets_per_job": 5,
                "emphasize_keywords": ["machine learning", "ai", "neural", "deep learning"],
            },
            "v1.3.0-fullstack": {
                "description": "Full-stack variant",
                "summary_key": "fullstack",
                "skill_sections": ["programming", "frameworks", "databases", "cloud"],
                "max_bullets_per_job": 4,
                "emphasize_keywords": ["frontend", "fullstack", "react", "javascript"],
            },
            "v1.4.0-devops": {
                "description": "DevOps-focused variant",
                "summary_key": "devops",
                "skill_sections": ["devops", "cloud", "databases", "programming"],
                "max_bullets_per_job": 4,
                "emphasize_keywords": ["devops", "kubernetes", "docker", "ci/cd"],
            },
            "v1.5.0-leadership": {
                "description": "Leadership-focused variant",
                "summary_key": "leadership",
                "skill_sections": ["programming", "frameworks", "devops", "cloud"],
                "max_bullets_per_job": 5,
                "emphasize_keywords": ["lead", "team", "mentor", "manage"],
            },
        },
    }


@pytest.fixture
def sample_yaml_file(temp_dir: Path, sample_resume_data: Dict[str, Any]) -> Path:
    """Create a sample resume.yaml file for testing."""
    yaml_path = temp_dir / "resume.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(sample_resume_data, f)
    return yaml_path


@pytest.fixture
def mock_config(temp_dir: Path) -> Config:
    """Create a mock Config instance with temp paths."""
    config_data = {
        "output": {
            "directory": str(temp_dir / "output"),
            "naming_scheme": "resume-{variant}-{date}.{ext}",
            "date_format": "%Y-%m-%d",
        },
        "tracking": {
            "enabled": True,
            "csv_path": str(temp_dir / "tracking" / "resume_experiment.csv"),
        },
        "github": {"username": "testuser", "sync_months": 3},
    }

    config = Config()
    config._merge_config(config_data)
    return config


@pytest.fixture
def yaml_handler(sample_yaml_file: Path) -> ResumeYAML:
    """Create a ResumeYAML instance with test data."""
    return ResumeYAML(sample_yaml_file)


@pytest.fixture
def sample_csv_file(temp_dir: Path) -> Path:
    """Create a sample CSV file for testing."""
    csv_path = temp_dir / "sample_tracking.csv"
    import csv

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "company",
                "position",
                "role",
                "status",
                "applied_date",
                "response_date",
                "resume_version",
                "cover_letter",
                "notes",
            ]
        )
        writer.writerow(
            [
                "Test Company",
                "Software Engineer",
                "Senior",
                "applied",
                "2024-01-15",
                "",
                "v1.0.0-base",
                "Yes",
                "Test note",
            ]
        )
    return csv_path
