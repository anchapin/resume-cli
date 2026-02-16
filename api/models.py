from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ResumeRequest(BaseModel):
    resume_data: Dict[str, Any]
    variant: str = "base"


class TailorRequest(BaseModel):
    resume_data: Dict[str, Any]
    job_description: str


class ATSRequest(BaseModel):
    resume_data: Dict[str, Any]
    variant: str = "v1.0.0-base"
    job_description: str


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
    resume_data: Dict[str, Any]
    job_description: str
    company_name: Optional[str] = None
    variant: str = "v1.0.0-base"
    format: str = "md"
    non_interactive: bool = False
    motivation: Optional[str] = None
    company_resonance: Optional[str] = None
    connections: Optional[str] = None

