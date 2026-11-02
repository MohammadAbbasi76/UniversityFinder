# Import universities into PostgreSQL

Run commands from the project root. PostgreSQL and the `universities` database
must already exist, with the `university` user owning the database.

```bash
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL='postgresql://university:YOUR_PASSWORD@localhost:5432/universities'
python main.py Germany
python main.py "United States"
python main.py DE
```

You can also run the script without a country argument to enter one when
prompted:

```bash
python main.py
```

Replace YOUR_PASSWORD with your password; URL-encode special characters in it.
Keep credentials out of source control. Environment variables are read directly;
the script does not automatically load a `.env` file.

The script downloads the worldwide JSON from
[Hipo](https://github.com/Hipo/university-domains-list), filters by ISO country
code, creates `hipo_universities`, and writes that country's records in one
transaction. It prints the number of unique records imported/updated.
It does not create the PostgreSQL server or database.

Validate without a database, or import an existing downloaded Hipo JSON file:

```bash
python main.py Germany --dry-run
python main.py Germany --file germany_universities.json
```

Repeated imports update source fields while retaining IDs and `extra_info`.
Records absent from later downloads are retained. Hipo has no stable institution
IDs: this importer matches by country code, exact name and state/province.
A renamed institution can create a new row; review such changes manually.
Conflicting source rows with the same key are rejected instead of silently merged.
An empty source state/province is stored as an empty string.
Coverage is limited to Hipo's records, not a guarantee of all universities.
Local JSON imports are expected to be unmodified Hipo-format records.

## Query saved records

```bash
psql -h localhost -U university -d universities -W
```

```sql
SELECT id, name, country, state_province, websites, domains, extra_info
FROM hipo_universities
WHERE country_code = 'DE'
ORDER BY name;
```

## Add information to one university later

Use an ID returned by the SELECT above (42 here is only an example).
JSONB accepts strings, numbers, lists and nested objects without adding columns:

```sql
UPDATE hipo_universities
SET extra_info = extra_info || '{"city":"Berlin","departments":["Computer Science"]}'::jsonb
WHERE id = 42
RETURNING id, name, extra_info;
```

This merges top-level keys and replaces values for keys already present.
Imported Hipo fields and your additions remain separate, so reimporting does not
erase custom information. Use dedicated related tables later for programmes,
admission cycles and other structured collections.
