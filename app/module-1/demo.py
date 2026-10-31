"""Small end-to-end demo of UniversityStore."""

from university_store import UniversityStore

SEED = {
    "Germany": [
        {
            "name": "TU München",
            "city": "Munich",
            "founded": 1868,
            "departments": ["Mechanical Engineering", "Informatics", "Physics"],
        },
        {
            "name": "RWTH Aachen",
            "city": "Aachen",
            "founded": 1870,
            "departments": ["Mechanical Engineering", "Electrical Engineering"],
        },
    ],
    "Iran": [
        {
            "name": "Sharif University of Technology",
            "city": "Tehran",
            "founded": 1966,
            "departments": ["Mechanical Engineering", "Computer Engineering"],
        }
    ],
    "Netherlands": [
        {
            "name": "TU Delft",
            "city": "Delft",
            "founded": 1842,
            "departments": ["Aerospace Engineering", "Mechanical Engineering"],
        }
    ],
}


def main() -> None:
    store = UniversityStore()
    store.flush()

    for country, unis in SEED.items():
        store.put_country(country, unis)

    print("countries:")
    for code, name, count in store.list_countries():
        print(f"  {code}  {name:<15} {count} universities")

    print("\nget_country('germany'):")
    for uni in store.get_country("germany"):
        print(f"  {uni['name']} ({uni['city']}, {uni['founded']}) -> {uni['departments']}")

    print("\nsame data via the German spelling 'Deutschland':")
    print(f"  {[u['name'] for u in store.get_country('Deutschland')]}")

    print("\nget_university('DE', 'tu-munchen'):")
    print(f"  {store.get_university('DE', 'tu-munchen')}")

    print("\nfind_by_department('mechanical engineering'):")
    for uni in store.find_by_department("mechanical engineering"):
        print(f"  [{uni['country']}] {uni['name']}")

    print("\nadd one university to an existing country:")
    store.put_university("Germany", {"name": "FU Berlin", "city": "Berlin", "departments": ["Physics"]})
    print(f"  Germany now has {len(store.get_country('de'))} universities")
    print(f"  last updated: {store.updated_at('Germany')}")

    store.export_json_file("/tmp/universities_export.json")
    store.snapshot()
    print("\nexported to /tmp/universities_export.json and snapshotted to disk")


if __name__ == "__main__":
    main()
