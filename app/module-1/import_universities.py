"""Import a country's Hipo universities into PostgreSQL. See POSTGRES.md."""

import argparse
import json
import os
import sys
from pathlib import Path

import psycopg
import pycountry
import requests
from psycopg.types.json import Jsonb

SOURCE_URL = (
    "https://raw.githubusercontent.com/Hipo/university-domains-list/"
    "master/world_universities_and_domains.json"
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS hipo_universities (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    country_code CHAR(2) NOT NULL,
    state_province TEXT NOT NULL DEFAULT '',
    websites TEXT[] NOT NULL,
    domains TEXT[] NOT NULL,
    source_url TEXT NOT NULL,
    source_record JSONB NOT NULL,
    extra_info JSONB NOT NULL DEFAULT '{}'::jsonb
        CHECK (jsonb_typeof(extra_info) = 'object'),
    imported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (country_code, name, state_province)
);
CREATE INDEX IF NOT EXISTS hipo_universities_country_idx
    ON hipo_universities (country_code);
"""

UPSERT = """
INSERT INTO hipo_universities
    (name, country, country_code, state_province, websites, domains,
     source_url, source_record)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (country_code, name, state_province) DO UPDATE SET
    country = EXCLUDED.country,
    websites = EXCLUDED.websites,
    domains = EXCLUDED.domains,
    source_url = EXCLUDED.source_url,
    source_record = EXCLUDED.source_record,
    imported_at = NOW()
"""


def resolve_country(value):
    aliases = {"uk": "GB", "south korea": "KR", "deutschland": "DE"}
    value = value.strip()
    if not value:
        raise ValueError("Country must not be empty.")
    try:
        return pycountry.countries.lookup(aliases.get(value.lower(), value))
    except LookupError:
        raise ValueError(f"Unknown country: {value!r}. Try its ISO code, e.g. DE.") from None


def select_country(data, code):
    if not isinstance(data, list):
        raise TypeError("Expected a JSON array of university records.")
    selected = {}
    for record in data:
        if not isinstance(record, dict):
            raise TypeError("Each university must be a JSON object.")
        record_code = record.get("alpha_two_code")
        if not isinstance(record_code, str):
            raise TypeError("University record has an invalid alpha_two_code.")
        if record_code.upper() != code:
            continue
        for field in ("name", "country"):
            if not isinstance(record.get(field), str) or not record[field].strip():
                raise ValueError(f"University record has an invalid {field}.")
        state = record.get("state-province")
        if state is not None and not isinstance(state, str):
            raise ValueError("Invalid state-province.")
        for field in ("web_pages", "domains"):
            values = record.get(field)
            if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
                raise ValueError(f"Invalid {field} for {record['name']}.")
        key = (record["name"], state or "")
        if key in selected and selected[key] != record:
            raise ValueError(f"Conflicting source records for {key}; review before importing.")
        selected[key] = record
    return list(selected.values())


def import_records(dsn, records):
    # Schema and all records commit together; errors roll the transaction back.
    with psycopg.connect(dsn, connect_timeout=10) as connection, connection.cursor() as cursor:
        cursor.execute(SCHEMA)
        cursor.executemany(UPSERT, [
            (r["name"], r["country"], r["alpha_two_code"].upper(),
             r.get("state-province") or "", r["web_pages"], r["domains"],
             SOURCE_URL, Jsonb(r))
            for r in records
        ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("country", nargs="?", help='Country name or code, e.g. "Germany" or DE')
    parser.add_argument("--file", type=Path, help="Read an existing Hipo JSON file instead of downloading")
    parser.add_argument("--dry-run", action="store_true", help="Validate and count without accessing PostgreSQL")
    args = parser.parse_args()
    try:
        country_input = args.country
        if country_input is None:
            country_input = input("Enter a country name or ISO code: ")
        country = resolve_country(country_input)
        dsn = os.environ.get("DATABASE_URL")
        if not args.dry_run and not dsn:
            raise ValueError("Set DATABASE_URL before importing. See POSTGRES.md.")
        if args.file:
            data = json.loads(args.file.read_text(encoding="utf-8"))
        else:
            response = requests.get(SOURCE_URL, timeout=(10, 60))
            response.raise_for_status()
            data = response.json()
        records = select_country(data, country.alpha_2)
        if not records:
            raise ValueError(f"No Hipo records found for {country.name}; nothing was written.")
        if args.dry_run:
            print(f"Validated {len(records)} universities for {country.name} ({country.alpha_2}). No database writes.")
        else:
            import_records(dsn, records)
            print(f"Imported/updated {len(records)} universities for {country.name} ({country.alpha_2}).")
    except psycopg.Error:
        # Avoid printing credentials from connection strings or server errors.
        print("Database import failed. Check PostgreSQL, credentials, permissions and table schema. No partial import was committed.", file=sys.stderr)
        return 1
    except (TypeError, ValueError, OSError, requests.RequestException) as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
