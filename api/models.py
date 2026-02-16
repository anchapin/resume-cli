from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ResumeRequest(BaseModel):
    """Request model for rendering a resume as PDF."""
    resume_data: Dict[str, Any] = Field(
        ...,
        description="Resume data in YAML-compatible dictionary format",
        examples=[{
            "contact": {"name": "John Doe", "email": "john@example.com"},
            "summary": "Experienced software engineer",
            "skills": {"languages": ["Python", "JavaScript"]},
            "experience": [{"company": "Tech Corp", "title": "Engineer"}]
        }]
    )
    variant: str = Field(
        default="base",
        description="Resume variant to use for generation",
        examples=["base", "v1.0.0-base", "v1.1.0-backend"]
    )


class TailorRequest(BaseModel):
    """Request model for AI-tailoring resume data to a job description."""
    resume_data: Dict[str, Any] = Field(
        ...,
        description="Resume data in YAML-compatible dictionary format",
        examples=[{
            "contact": {"name": "John Doe", "email": "john@example.com"},
            "summary": "Experienced software engineer",
            "skills": {"languages": ["Python", "JavaScript"]},
            "experience": [{"company": "Tech Corp", "title": "Engineer"}]
        }]
    )
    job_description: str = Field(
        ...,
        description="Job description text to tailor resume against",
        examples=["Senior Backend Engineer\\nRequirements:\\n- Python\\n- FastAPI"]
    )


class ATSRequest(BaseModel):
    """Request model for ATS compatibility check."""
    resume_data: Dict[str, Any] = Field(
        ...,
        description="Resume data in YAML-compatible dictionary format",
        examples=[{
            "contact": {"name": "John Doe", "email": "john@example.com"},
            "summary": "Experienced software engineer",
            "skills": {"languages": ["Python", "JavaScript"]},
            "experience": [{"company": "Tech Corp", "title": "Engineer"}]
        }]
    )
    variant: str = Field(
        default="v1.0.0-base",
        description="Resume variant to check for ATS compatibility",
        examples=["v1.0.0-base", "v1.1.0-backend"]
    )
    job_description: str = Field(
        ...,
        description="Job description text to analyze against",
        examples=["Senior Backend Engineer\\nRequirements:\\n- Python\\n- FastAPI"]
    )


class ATSCategoryScore(BaseModel):
    name: str
    score: float
    max_score: float
    percentage: float
    details: Dict[str, Any] = {}


class ATSReport(BaseModel):
    overall_score: float
    overall_max_score: float
    overall_percentage: float
    categories: List[ATSCategoryScore]
    suggestions: List[str] = []
    missing_keywords: List[str] = []
    matching_keywords: List[str] = []


class CoverLetterRequest(BaseModel):
    """Request model for generating a cover letter."""
    resume_data: Dict[str, Any] = Field(
        ...,
        description="Resume data in YAML-compatible dictionary format",
        examples=[{
            "contact": {"name": "John Doe", "email": "john@example.com"},
            "summary": "Experienced software engineer",
            "skills": {"languages": ["Python", "JavaScript"]},
            "experience": [{"company": "Tech Corp", "title": "Engineer"}]
        }]
    )
    job_description: str = Field(
        ...,
        description="Job description text for the position",
        examples=["Senior Backend Engineer at Tech Corp\\nRequirements:\\n- Python\\n- FastAPI"]
    )
    company_name: Optional[str] = Field(
        default=None,
        description="Name of the company to generate cover letter for",
        examples=["Tech Corp", "Acme Inc"]
    )
    variant: str = Field(
        default="v1.0.0-base",
        description="Resume variant to use as base for cover letter",
        examples=["v1.0.0-base", "v1.1.0-backend"]
    )
    format: str = Field(
        default="md",
        description="Output format for cover letter",
        examples=["md", "pdf"]
    )
    non_interactive: bool = Field(
        default=False,
        description="Use non-interactive mode (AI-generated responses) instead of user prompts"
    )
    motivation: Optional[str] = Field(
        default=None,
        description="User's motivation for applying to this role",
        examples=["Passion for building scalable systems"]
    )
    company_resonance: Optional[str] = Field(
        default=None,
        description="Aspects of company mission or culture that resonate with user",
        examples=["Innovation in AI technology"]
    )
    connections: Optional[str] = Field(
        default=None,
        description="Any connections at the company (e.g., referrals)",
        examples=["Know someone on the engineering team"]
    )
