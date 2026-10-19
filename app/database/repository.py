from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from app.schemas.university import ProgramRecord, ProfessorRecord, UniversitySummary


class UniversityRepository:
    def __init__(self) -> None:
        self.universities: Dict[str, UniversitySummary] = {}
        self.programs: Dict[str, List[dict]] = defaultdict(list)
        self.professors: Dict[str, List[dict]] = defaultdict(list)
        self._seed_default_data()

    def _seed_default_data(self) -> None:
        university_data = [
            {
                "id": "utoronto",
                "name": "University of Toronto",
                "country": "Canada",
                "country_code": "CA",
                "website": "https://www.utoronto.ca",
                "city": "Toronto",
                "province": "Ontario",
                "verified": True,
                "institution_type": "University",
                "verification_source": "Official website",
            },
            {
                "id": "ubc",
                "name": "University of British Columbia",
                "country": "Canada",
                "country_code": "CA",
                "website": "https://www.ubc.ca",
                "city": "Vancouver",
                "province": "British Columbia",
                "verified": True,
                "institution_type": "University",
                "verification_source": "Official directory",
            },
            {
                "id": "mcgill",
                "name": "McGill University",
                "country": "Canada",
                "country_code": "CA",
                "website": "https://www.mcgill.ca",
                "city": "Montreal",
                "province": "Quebec",
                "verified": True,
                "institution_type": "University",
                "verification_source": "Official directory",
            },
            {
                "id": "harvard",
                "name": "Harvard University",
                "country": "United States",
                "country_code": "US",
                "website": "https://www.harvard.edu",
                "city": "Cambridge",
                "province": "Massachusetts",
                "verified": True,
                "institution_type": "University",
                "verification_source": "Official directory",
            },
            {
                "id": "lmu",
                "name": "Ludwig Maximilian University of Munich",
                "country": "Germany",
                "country_code": "DE",
                "website": "https://www.lmu.de",
                "city": "Munich",
                "province": "Bavaria",
                "verified": True,
                "institution_type": "University",
                "verification_source": "Official website",
            },
        ]

        for item in university_data:
            summary = UniversitySummary(
                id=item["id"],
                name=item["name"],
                country=item["country"],
                website=item["website"],
                city=item["city"],
                province=item["province"],
                verified=item["verified"],
                institution_type=item["institution_type"],
                verification_source=item["verification_source"],
            )
            self.universities[summary.id] = summary

        self.programs["utoronto"] = [
            {
                "id": "utoronto-msc-cs",
                "university_id": "utoronto",
                "name": "MSc Computer Science",
                "degree_level": "Master's",
                "department": "Computer Science",
                "language": "English",
                "tuition_fee": 25000.0,
                "application_deadline": "2027-01-15",
            }
        ]
        self.professors["utoronto"] = [
            {
                "id": "utoronto-prof-1",
                "university_id": "utoronto",
                "name": "Dr. Alex Chen",
                "department": "Computer Science",
                "research_interests": "Machine learning, distributed systems",
                "email": "alex.chen@utoronto.ca",
                "profile_url": "https://www.cs.toronto.edu/~alex/",
            }
        ]

    def list_all(self) -> List[UniversitySummary]:
        return list(self.universities.values())

    def get_by_country(self, country_code: str, country_name: str | None = None) -> List[UniversitySummary]:
        country_name_l = (country_name or "").lower()
        return [
            u
            for u in self.universities.values()
            if u.country.lower() == country_name_l or u.id in self._country_to_ids(country_code)
        ]

    def _country_to_ids(self, country_code: str) -> List[str]:
        mapping = {
            "CA": ["utoronto", "ubc", "mcgill"],
            "US": ["harvard"],
            "DE": ["lmu"],
        }
        return mapping.get(country_code.upper(), [])

    def get_by_id(self, university_id: str) -> UniversitySummary | None:
        return self.universities.get(university_id)

    def get_programs(self, university_id: str) -> List[dict]:
        return self.programs.get(university_id, [])

    def get_professors(self, university_id: str) -> List[dict]:
        return self.professors.get(university_id, [])


repository = UniversityRepository()
