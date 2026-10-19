from __future__ import annotations

import re
from typing import List

import pycountry

from app.database.repository import repository
from app.schemas.university import UniversitySummary
from app.validation.university_validator import validate_university


def get_country_code(country_name: str) -> str:
    if not country_name or not country_name.strip():
        raise ValueError("A country name is required.")

    normalized = country_name.strip()
    aliases = {
        "us": "US",
        "usa": "US",
        "united states": "US",
        "united states of america": "US",
        "canada": "CA",
        "ca": "CA",
        "germany": "DE",
        "de": "DE",
    }
    lower_name = normalized.lower()
    if lower_name in aliases:
        return aliases[lower_name]

    try:
        return pycountry.countries.lookup(normalized).alpha_2
    except LookupError:
        for country in pycountry.countries:
            official_name = getattr(country, "official_name", None)
            if country.name.lower() == lower_name or (official_name and official_name.lower() == lower_name):
                return country.alpha_2
        raise ValueError(f"Unsupported country: {country_name}")


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def deduplicate_universities(items: List[UniversitySummary]) -> List[UniversitySummary]:
    deduped: dict[str, UniversitySummary] = {}
    for item in items:
        key = normalize_name(item.name)
        if key not in deduped:
            deduped[key] = item
    return list(deduped.values())


def discover_universities(country_name: str, include_programs: bool = False, include_professors: bool = False) -> List[UniversitySummary]:
    country_code = get_country_code(country_name)
    country_results = repository.get_by_country(country_code, country_name)
    validated = [validate_university(item) for item in country_results]
    deduped = deduplicate_universities(validated)
    return deduped


def get_country_summary(country_name: str) -> dict:
    country_code = get_country_code(country_name)
    universities = discover_universities(country_name)
    return {
        "country": country_name,
        "country_code": country_code,
        "universities": [u.model_dump() for u in universities],
    }
