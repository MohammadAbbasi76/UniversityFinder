"""
University Discover - Redis-backed storage layer.

Data model (plain Redis, no modules required):

    SET   countries                 -> {"de", "ir", "us", ...}      ISO alpha-2 codes
    HASH  country:name              -> code -> display name ("de" -> "Germany")
    HASH  uni:<code>                -> slug -> JSON blob of one university
    HASH  dept:index                -> normalised dept -> packed "code/slug" list
    STRING meta:updated:<code>      -> ISO timestamp of last write for that country

One hash per country keeps each university independently readable and writable,
so updating a single record never rewrites the whole country blob.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any, Iterable, Iterator

import redis

try:
    import pycountry
except ImportError:  # optional dependency
    pycountry = None


# --------------------------------------------------------------------------
# key helpers
# --------------------------------------------------------------------------

KEY_COUNTRIES = "countries"
KEY_COUNTRY_NAME = "country:name"
KEY_DEPT_INDEX = "dept:index"


# Native / colloquial spellings pycountry does not know. Extend as needed.
COUNTRY_ALIASES: dict[str, str] = {
    "Germany": "DE",
    "Nederland": "NL",
    "Poland": "PL",
    "Austria": "AT",
    "Suisse": "CH",
    "Switzerland": "CH",
    "España": "ES",
    "UK": "GB",
    "England": "GB",
}


def register_alias(alias: str, alpha_2: str) -> None:
    COUNTRY_ALIASES[alias.strip().lower()] = alpha_2.upper()


def country_code(country: str) -> str:
    """Normalise any country spelling to a lowercase ISO alpha-2 code.

    'Germany', 'germany', 'Deutschland', 'DE', 'DEU' -> 'de'
    Falls back to a slug of the input when pycountry is unavailable or the
    name is unknown, so nothing is ever silently dropped.
    """
    raw = country.strip()
    if not raw:
        raise ValueError("country must not be empty")
    alias = COUNTRY_ALIASES.get(raw.lower())
    if alias:
        return alias.lower()
    if pycountry is not None:
        try:
            return pycountry.countries.lookup(raw).alpha_2.lower()
        except LookupError:
            pass
    return slugify(raw)


def country_display(country: str) -> str:
    raw = COUNTRY_ALIASES.get(country.strip().lower(), country.strip())
    if pycountry is not None:
        try:
            return pycountry.countries.lookup(raw).name
        except LookupError:
            pass
    return raw


def slugify(text: str) -> str:
    """'TU München' -> 'tu-munchen'   (stable id for a university record)"""
    norm = unicodedata.normalize("NFKD", text)
    ascii_only = norm.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_only.lower()).strip("-")


def _norm_dept(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


# --------------------------------------------------------------------------
# store
# --------------------------------------------------------------------------

class UniversityStore:
    """country name in -> universities (and their departments) out."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        client: redis.Redis | None = None,
    ) -> None:
        self.r = client or redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,  # str in, str out - no manual .decode()
        )

    # -- write ------------------------------------------------------------

    def put_university(self, country: str, university: dict[str, Any]) -> str:
        """Insert or replace one university. Returns its slug."""
        code = country_code(country)
        slug = university.get("slug") or slugify(university["name"])
        record = dict(university, slug=slug)

        pipe = self.r.pipeline()
        pipe.sadd(KEY_COUNTRIES, code)
        pipe.hset(KEY_COUNTRY_NAME, code, country_display(country))
        pipe.hset(f"uni:{code}", slug, json.dumps(record, ensure_ascii=False))
        pipe.set(f"meta:updated:{code}", datetime.now(timezone.utc).isoformat())
        for dept in record.get("departments", []):
            pipe.sadd(f"dept:{_norm_dept(dept)}", f"{code}/{slug}")
        pipe.execute()
        return slug

    def put_country(self, country: str, universities: Iterable[dict[str, Any]]) -> int:
        """Replace a country's entire list of universities."""
        code = country_code(country)
        self.delete_country(code)
        count = 0
        for uni in universities:
            self.put_university(code, uni)
            count += 1
        return count

    def delete_country(self, country: str) -> None:
        code = country_code(country)
        for uni in self.get_country(code):
            for dept in uni.get("departments", []):
                self.r.srem(f"dept:{_norm_dept(dept)}", f"{code}/{uni['slug']}")
        pipe = self.r.pipeline()
        pipe.delete(f"uni:{code}")
        pipe.delete(f"meta:updated:{code}")
        pipe.srem(KEY_COUNTRIES, code)
        pipe.hdel(KEY_COUNTRY_NAME, code)
        pipe.execute()

    # -- read -------------------------------------------------------------

    def get_country(self, country: str) -> list[dict[str, Any]]:
        """All universities of one country. This is the O(1) hot path."""
        code = country_code(country)
        blobs = self.r.hgetall(f"uni:{code}")
        return [json.loads(v) for v in blobs.values()]

    def get_university(self, country: str, slug: str) -> dict[str, Any] | None:
        blob = self.r.hget(f"uni:{country_code(country)}", slug)
        return json.loads(blob) if blob else None

    def list_countries(self) -> list[tuple[str, str, int]]:
        """[(code, display name, university count)] sorted by name."""
        out = []
        for code in self.r.smembers(KEY_COUNTRIES):
            name = self.r.hget(KEY_COUNTRY_NAME, code) or code
            out.append((code, name, self.r.hlen(f"uni:{code}")))
        return sorted(out, key=lambda row: row[1])

    def updated_at(self, country: str) -> str | None:
        return self.r.get(f"meta:updated:{country_code(country)}")

    def find_by_department(self, department: str) -> list[dict[str, Any]]:
        """Reverse lookup via the dept: sets - still O(1), no key scan."""
        members = self.r.smembers(f"dept:{_norm_dept(department)}")
        hits = []
        for member in sorted(members):
            code, slug = member.split("/", 1)
            uni = self.get_university(code, slug)
            if uni:
                hits.append(dict(uni, country=code))
        return hits

    def iter_universities(self) -> Iterator[tuple[str, dict[str, Any]]]:
        """Full walk, cursor-based so it never blocks the server."""
        for key in self.r.scan_iter(match="uni:*", count=100):
            code = key.split(":", 1)[1]
            for blob in self.r.hvals(key):
                yield code, json.loads(blob)

    # -- bulk / persistence ------------------------------------------------

    def load_json_file(self, path: str) -> int:
        """Import {"Germany": [ {...}, {...} ], "Iran": [...]} from disk."""
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return sum(self.put_country(c, unis) for c, unis in data.items())

    def export_json_file(self, path: str) -> None:
        data: dict[str, list[dict[str, Any]]] = {}
        for code, name, _ in self.list_countries():
            data[name] = self.get_country(code)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)

    def snapshot(self) -> None:
        """Force an RDB write to disk now (non-blocking background save)."""
        try:
            self.r.bgsave()
        except redis.ResponseError:
            pass  # a save is already in progress

    def flush(self) -> None:
        self.r.flushdb()


# --------------------------------------------------------------------------
# CLI — so that `python university_store.py` actually does something
# --------------------------------------------------------------------------

_SAMPLE = {
    "Germany": [
        {"name": "TU München", "city": "Munich", "founded": 1868,
         "departments": ["Mechanical Engineering", "Informatics", "Physics"]},
        {"name": "RWTH Aachen", "city": "Aachen", "founded": 1870,
         "departments": ["Mechanical Engineering", "Electrical Engineering"]},
    ],
    "Iran": [
        {"name": "Sharif University of Technology", "city": "Tehran", "founded": 1966,
         "departments": ["Mechanical Engineering", "Computer Engineering"]},
    ],
}


def _main(argv: list[str]) -> int:
    import argparse

    p = argparse.ArgumentParser(description="University Discover store CLI")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=6379)
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("status", help="connection + dataset summary (default)")
    sub.add_parser("seed", help="write a small sample dataset")
    g = sub.add_parser("get", help="list universities of one country")
    g.add_argument("country")
    d = sub.add_parser("dept", help="find universities by department")
    d.add_argument("department")
    l = sub.add_parser("load", help="bulk import a JSON file")
    l.add_argument("path")
    e = sub.add_parser("export", help="dump everything to a JSON file")
    e.add_argument("path")

    args = p.parse_args(argv)
    store = UniversityStore(host=args.host, port=args.port)

    try:
        store.r.ping()
    except redis.ConnectionError as exc:
        print(f"cannot reach redis at {args.host}:{args.port} -> {exc}")
        return 1

    cmd = args.cmd or "status"

    if cmd == "status":
        countries = store.list_countries()
        total = sum(c[2] for c in countries)
        print(f"connected to redis {args.host}:{args.port}")
        print(f"{len(countries)} countries, {total} universities")
        for code, name, count in countries:
            print(f"  {code}  {name:<30} {count}")
        if not countries:
            print("  (database is empty — run: python university_store.py seed)")

    elif cmd == "seed":
        for country, unis in _SAMPLE.items():
            store.put_country(country, unis)
        store.snapshot()
        print(f"seeded {len(_SAMPLE)} countries")

    elif cmd == "get":
        unis = store.get_country(args.country)
        if not unis:
            print(f"no data for {args.country!r}")
            return 1
        for uni in sorted(unis, key=lambda u: u["name"]):
            print(f"{uni['name']} ({uni.get('city', '?')}) -> {', '.join(uni.get('departments', []))}")

    elif cmd == "dept":
        for uni in store.find_by_department(args.department):
            print(f"[{uni['country']}] {uni['name']}")

    elif cmd == "load":
        print(f"imported {store.load_json_file(args.path)} universities")
        store.snapshot()

    elif cmd == "export":
        store.export_json_file(args.path)
        print(f"written {args.path}")

    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))