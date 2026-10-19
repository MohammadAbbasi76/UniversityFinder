from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.university import UniversitySummary


class DiscoveryRequest(BaseModel):
    country: str = Field(..., min_length=2)
    include_programs: bool = False
    include_professors: bool = False


class DiscoveryJobResponse(BaseModel):
    job_id: str
    country: str
    status: str = "completed"
    message: str
    university_count: int = 0
    universities: List[UniversitySummary] = Field(default_factory=list)


class DiscoveryStatusResponse(BaseModel):
    job_id: str
    country: str
    status: str
    message: str
    university_count: int = 0
    universities: List[UniversitySummary] = Field(default_factory=list)
