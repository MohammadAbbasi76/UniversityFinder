from __future__ import annotations

import uuid
from typing import Dict

from fastapi import APIRouter, HTTPException

from app.discovery.discovery_manager import discover_universities, get_country_code
from app.schemas.discovery import DiscoveryJobResponse, DiscoveryRequest, DiscoveryStatusResponse

router = APIRouter()

jobs: Dict[str, DiscoveryStatusResponse] = {}


@router.post("/discover", response_model=DiscoveryJobResponse)
def start_discovery(payload: DiscoveryRequest):
    try:
        country_code = get_country_code(payload.country)
        universities = discover_universities(payload.country, payload.include_programs, payload.include_professors)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    job_id = str(uuid.uuid4())
    response = DiscoveryStatusResponse(
        job_id=job_id,
        country=payload.country,
        status="completed",
        message="University discovery completed successfully.",
        university_count=len(universities),
        universities=universities,
    )
    jobs[job_id] = response
    return DiscoveryJobResponse(
        job_id=job_id,
        country=payload.country,
        status=response.status,
        message=response.message,
        university_count=response.university_count,
        universities=response.universities,
    )


@router.get("/jobs/{job_id}", response_model=DiscoveryStatusResponse)
def get_job_status(job_id: str):
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job
