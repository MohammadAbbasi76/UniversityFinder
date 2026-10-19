from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class UniversitySummary(BaseModel):
    id: str
    name: str
    country: str
    website: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    verified: bool = False
    institution_type: str = "University"
    verification_source: Optional[str] = None


class UniversityDetail(UniversitySummary):
    programs: List[dict[str, Any]] = Field(default_factory=list)
    professors: List[dict[str, Any]] = Field(default_factory=list)


class ProgramRecord(BaseModel):
    id: str
    university_id: str
    name: str
    degree_level: str
    department: str
    language: str = "English"
    tuition_fee: Optional[float] = None
    application_deadline: Optional[str] = None


class ProfessorRecord(BaseModel):
    id: str
    university_id: str
    name: str
    department: str
    research_interests: str = ""
    email: Optional[str] = None
    profile_url: Optional[str] = None
