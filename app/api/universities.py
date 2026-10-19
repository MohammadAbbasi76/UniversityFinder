from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.database.repository import repository
from app.discovery.discovery_manager import get_country_code

router = APIRouter()


@router.get("/universities")
def list_universities(country: str | None = Query(default=None)):
    if country:
        try:
            country_code = get_country_code(country)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        universities = repository.get_by_country(country_code, country)
    else:
        universities = repository.list_all()
    return [u.model_dump() for u in universities]


@router.get("/universities/{university_id}")
def get_university(university_id: str):
    university = repository.get_by_id(university_id)
    if university is None:
        raise HTTPException(status_code=404, detail="University not found.")
    response = university.model_dump()
    response["programs"] = repository.get_programs(university_id)
    response["professors"] = repository.get_professors(university_id)
    return response


@router.get("/universities/{university_id}/programs")
def get_university_programs(university_id: str):
    if repository.get_by_id(university_id) is None:
        raise HTTPException(status_code=404, detail="University not found.")
    return repository.get_programs(university_id)


@router.get("/universities/{university_id}/professors")
def get_university_professors(university_id: str):
    if repository.get_by_id(university_id) is None:
        raise HTTPException(status_code=404, detail="University not found.")
    return repository.get_professors(university_id)
