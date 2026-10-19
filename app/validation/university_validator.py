from __future__ import annotations

from app.schemas.university import UniversitySummary


def validate_university(record: UniversitySummary) -> UniversitySummary:
    if not record.website:
        record.verified = False
        record.verification_source = "Missing official website"
        return record

    if "http" not in record.website:
        record.verified = False
        record.verification_source = "Website is not an official URL"
        return record

    if "university" in record.name.lower() or any(word in record.website.lower() for word in ("edu", ".ac", ".edu")):
        record.verified = True
        record.verification_source = record.verification_source or "Domain verification"
    return record
