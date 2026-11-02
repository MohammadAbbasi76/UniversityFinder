import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app" / "module-1"))

import import_universities

import main as project_main


def university(name, country_code="DE", **overrides):
    record = {
        "alpha_two_code": country_code,
        "name": name,
        "country": "Germany" if country_code == "DE" else "France",
        "state-province": None,
        "web_pages": [f"https://{name.lower().replace(' ', '')}.example"],
        "domains": [f"{name.lower().replace(' ', '')}.example"],
    }
    record.update(overrides)
    return record


def test_select_country_filters_and_deduplicates_records():
    duplicate = university("Example University")
    records = [
        duplicate,
        duplicate.copy(),
        university("Université Exemple", country_code="FR"),
    ]

    assert import_universities.select_country(records, "DE") == [duplicate]


def test_select_country_rejects_conflicting_duplicates():
    first = university("Example University")
    second = university("Example University", domains=["different.example"])

    with pytest.raises(ValueError, match="Conflicting source records"):
        import_universities.select_country([first, second], "DE")


@pytest.mark.parametrize(
    "records",
    [
        {},
        [None],
        [{"alpha_two_code": None}],
        [university("Missing websites", web_pages=None)],
        [dict(university("Missing name"), name=" ")],
    ],
)
def test_select_country_rejects_malformed_records(records):
    with pytest.raises((TypeError, ValueError)):
        import_universities.select_country(records, "DE")


def test_main_prompts_for_country_and_dry_run_needs_no_database(
    monkeypatch, capsys, tmp_path
):
    data_file = tmp_path / "universities.json"
    data_file.write_text(
        json.dumps([university("Example University")]), encoding="utf-8"
    )
    monkeypatch.setattr("sys.argv", ["import_universities.py", "--file", str(data_file), "--dry-run"])
    monkeypatch.setattr("builtins.input", lambda _: "Germany")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert import_universities.main() == 0
    assert "Validated 1 universities for Germany (DE)" in capsys.readouterr().out


def test_resolve_country_accepts_names_codes_and_aliases():
    assert import_universities.resolve_country("Germany").alpha_2 == "DE"
    assert import_universities.resolve_country("DE").alpha_2 == "DE"
    assert import_universities.resolve_country("Deutschland").alpha_2 == "DE"


def test_project_main_runs_modules_in_order_and_forwards_arguments(monkeypatch):
    calls = []

    class Result:
        returncode = 0

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return Result()

    monkeypatch.setattr("sys.argv", ["main.py", "Germany", "--dry-run"])
    monkeypatch.setattr(project_main.subprocess, "run", fake_run)

    assert project_main.main() == 0
    assert len(calls) == 1
    assert calls[0][0][1:] == [
        str(project_main.PROJECT_ROOT / "app" / "module-1" / "import_universities.py"),
        "Germany",
        "--dry-run",
    ]