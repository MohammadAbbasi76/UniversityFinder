# University Discover — Redis storage layer

A `country name → universities (+ departments)` store on Redis, kept in RAM and
persisted to disk with both RDB snapshots and AOF.

## 1. Architecture

```
            put_country("Germany", [...])            get_country("Deutschland")
                        │                                        │
                        ▼                                        ▼
            ┌─────────────────────────────────────────────────────────┐
            │  UniversityStore  (university_store.py)                 │
            │  • country_code()  name → ISO alpha-2  (pycountry +     │
            │                     alias map: Deutschland/ایران/UK…)   │
            │  • slugify()       "TU München" → "tu-munchen"          │
            │  • pipeline()      one round-trip per write             │
            └─────────────────────────────────────────────────────────┘
                        │ RESP protocol, :6379
                        ▼
            ┌─────────────────────────────────────────────────────────┐
            │  redis-server            (entire dataset lives in RAM)  │
            │                                                         │
            │  SET    countries          {de, ir, nl, …}              │
            │  HASH   country:name       de → "Germany"               │
            │  HASH   uni:de             tu-munchen → {JSON}          │
            │                            rwth-aachen → {JSON}         │
            │  SET    dept:mechanical engineering  {de/tu-munchen, …} │
            │  STRING meta:updated:de    2026-10-20T16:16:00Z         │
            └─────────────────────────────────────────────────────────┘
                        │ fork + write (background, never blocks reads)
                        ▼
            rdata/universities.rdb              ← periodic snapshot
            rdata/appendonlydir/*.aof           ← every write, fsync 1×/s
```

Why a **hash per country** instead of one JSON string per country:

| approach | read all | read one uni | update one uni |
|---|---|---|---|
| `SET country:de '<big json>'` | O(1) | parse whole blob | **rewrite whole blob** |
| `HASH uni:de` (this design) | `HGETALL` | `HGET` | `HSET` on one field |

The `dept:*` sets are a hand-built reverse index, so "which universities teach
mechanical engineering" stays O(1) instead of scanning every key.

## 2. Setup

```bash
sudo apt install redis-server          # or: docker run -p 6379:6379 redis:7
pip install redis pycountry
```

`redis.conf` — the part that matters for "RAM **and** disk":

```conf
dir /var/lib/redis/universities
dbfilename universities.rdb

save 900 1        # snapshot if ≥1 key changed in 15 min
save 300 10
save 60 1000

appendonly yes    # log every write
appendfsync everysec   # at most 1 s of data at risk
```

Run it:

```bash
redis-server /path/to/redis.conf --daemonize yes
redis-cli ping     # PONG
```

On startup Redis replays the AOF (it takes precedence over the RDB), so the
dataset is back in RAM before the first client connects.

## 3. Usage

```python
from university_store import UniversityStore

store = UniversityStore()                      # 127.0.0.1:6379

store.put_country("Germany", [
    {"name": "TU München", "city": "Munich", "founded": 1868,
     "departments": ["Mechanical Engineering", "Informatics"]},
])

store.get_country("germany")        # same as "Deutschland", "DE", "DEU"
store.get_university("DE", "tu-munchen")
store.find_by_department("mechanical engineering")
store.list_countries()              # [(code, name, count), …]

store.load_json_file("universities.json")      # bulk import
store.export_json_file("backup.json")          # human-readable backup
store.snapshot()                               # force BGSAVE now
```

Input JSON format for `load_json_file`:

```json
{
  "Germany": [
    {"name": "TU München", "city": "Munich", "departments": ["Physics"]}
  ],
  "Iran": [
    {"name": "Sharif University of Technology", "departments": ["Mechanical Engineering"]}
  ]
}
```

## 4. Verified behaviour

Run against a real `redis-server 7.x`:

```
countries:
  de  Germany         3 universities
  ir  Iran            1 universities
  nl  Netherlands     1 universities

find_by_department('mechanical engineering'):
  [de] RWTH Aachen
  [de] TU München
  [ir] Sharif University of Technology
  [nl] TU Delft

--- redis-cli shutdown nosave, then restart ---
after restart: [('de', 'Germany', 3), ('ir', 'Iran', 1), ('nl', 'Netherlands', 1)]
```

`shutdown nosave` skips the final snapshot deliberately — the data comes back
from the AOF, which proves durability is real and not just a lucky RDB write.

## 5. Operational notes

- **Memory**: a few hundred countries with thousands of universities is tens of
  MB. Check with `redis-cli info memory` / `MEMORY USAGE uni:de`.
- **`maxmemory-policy noeviction`** is set on purpose. This is a database, not a
  cache; you never want Redis silently dropping countries under pressure.
- **Never `KEYS *`** in application code. `iter_universities()` uses `SCAN`.
- **Backups**: copy `universities.rdb` while the server runs, or call
  `export_json_file()` for a diffable, git-friendly dump.
- **Limits**: Redis has no joins, no `WHERE founded < 1900`, no fuzzy search.
  Every query pattern needs its own index built by hand (as `dept:*` is). If
  such queries start piling up, move the source of truth to SQLite/Postgres and
  keep Redis only as the read cache.
