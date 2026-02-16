from typing import Any, Dict, Optional

from pydantic import BaseModel


class ResumeRequest(BaseModel):
    resume_data: Dict[str, Any]
    variant: str = "base"


class TailorRequest(BaseModel):
    resume_data: Dict[str, Any]
    job_description: str
