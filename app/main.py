import os, re, json, time, hashlib, csv
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from openai import OpenAI                    # OpenRouter is OpenAI-compatible

# ---------------- config ----------------
MODEL         = os.getenv("OPENROUTER_MODEL", "minimax/minimax-m3.1-flash:free")
UNIS_CSV      = Path(__file__).resolve().parent / "canadian_universities.csv"
OUT_FILE      = Path("output.json")
CACHE_DIR     = Path("cache"); CACHE_DIR.mkdir(exist_ok=True)
HEADERS       = {"User-Agent": "UniResearchBot/1.0 (you@example.com)"}

def get_client():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENROUTER_API_KEY before running this script.")
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        timeout=120,
        max_retries=0,
    )

# ---------------- helpers ----------------
def fetch(url, ttl=86400):
    """GET with on-disk HTML cache. Returns text or None."""
    key = hashlib.sha1(url.encode()).hexdigest()
    p   = CACHE_DIR / f"{key}.html"
    if p.exists() and (time.time() - p.stat().st_mtime) < ttl:
        return p.read_text(encoding="utf-8", errors="ignore")
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200 and "text/html" in r.headers.get("content-type", ""):
            p.write_text(r.text, encoding="utf-8")
            return r.text
    except Exception as e:
        print("  fetch err:", url, e)
    return None

def llm_json(prompt, retries=4):
    """Ask the free model for JSON, tolerate code fences."""
    client = get_client()
    for i in range(retries):
        try:
            parts = []
            with client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                stream=True,
            ) as stream:
                for chunk in stream:
                    if chunk.choices:
                        content = chunk.choices[0].delta.content
                        if content:
                            parts.append(content)
                            print(content, end="", flush=True)
                    if chunk.usage:
                        details = chunk.usage.completion_tokens_details
                        reasoning_tokens = details.reasoning_tokens if details else None
                        print(f"\nReasoning tokens: {reasoning_tokens}")
            print()
            txt = "".join(parts).strip()
            # strip ```json ... ```
            txt = re.sub(r"^```(?:json)?|```$", "", txt, flags=re.M).strip()
            # grab first array/object
            m = re.search(r"[\[{].*[\]}]", txt, re.S)
            if not m:
                raise ValueError("Model response did not contain JSON")
            return json.loads(m.group(0))
        except Exception as e:
            print(f"  LLM err {i+1}: {e}")
            if i + 1 < retries:
                time.sleep(4 * (i + 1))
    return None

def get_links(html, base_url):
    soup = BeautifulSoup(html, "lxml")
    out  = []
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        text = a.get_text(" ", strip=True)
        if text and href.startswith("http"):
            out.append({"text": text, "url": href})
    return out

def same_domain(a, b):
    return urlparse(a).netloc == urlparse(b).netloc

DEPT_HINT    = re.compile(r"(depart|facult|school|college|academic|program)", re.I)
FACULTY_HINT = re.compile(r"(faculty|people|staff|directory|professors|team|members|personnel)", re.I)

# ---------------- step 1: departments ----------------
def discover_departments(uni_name, uni_url):
    html = fetch(uni_url)
    if not html:
        return []
    links = get_links(html, uni_url)
    cands = [
        l for l in links
        if same_domain(l["url"], uni_url) and (DEPT_HINT.search(l["url"]) or DEPT_HINT.search(l["text"]))
    ]
    # dedupe by URL
    seen, uniq = set(), []
    for c in cands:
        if c["url"] not in seen:
            seen.add(c["url"]); uniq.append(c)
    if not uniq:
        return []

    prompt = f"""From the candidate links of the {uni_name} website, return ONLY the
academic departments / faculties / schools / colleges that offer degree programs.

Return a JSON array like:
[{{"name": "Department of Computer Science", "url": "https://..."}}]

Rules:
- Use only URLs from the CANDIDATES list, verbatim.
- Drop non-academic units: Admissions, Library, Alumni, News, Donate, Careers, Bookstore, IT Help, Student Life.
- Drop duplicates and near-duplicates (prefer the more general "Department of X" over "X 101").
- Cap the result at 80 items.
- If none qualify, return [].

CANDIDATES:
{json.dumps(uniq[:150], ensure_ascii=False)}
"""
    result = llm_json(prompt)
    return result if isinstance(result, list) else []

# ---------------- step 2: faculty page ----------------
def find_faculty_page(dept_url):
    html = fetch(dept_url)
    if not html:
        return dept_url
    links = get_links(html, dept_url)
    cands = [l for l in links if FACULTY_HINT.search(l["url"]) or FACULTY_HINT.search(l["text"])]
    if not cands:
        return dept_url

    # cheap win: pick by keyword score before bothering the LLM
    def score(l):
        u = (l["url"] + " " + l["text"]).lower()
        return sum(kw in u for kw in ("faculty", "people", "directory", "staff", "professors"))

    cands.sort(key=score, reverse=True)
    return cands[0]["url"]

# ---------------- step 3: professors ----------------
def extract_professors(html, page_url, uni_name, dept_name):
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = re.sub(r"\n{2,}", "\n", soup.get_text("\n", strip=True))[:8000]
    if len(text) < 200:
        return []

    prompt = f"""Extract the faculty / professors listed on this page.

University: {uni_name}
Department: {dept_name}
Page URL:  {page_url}

Return a JSON array. Each item:
{{"name": "Full Name", "title": "Assistant Professor", "email": "x@y.ca or null",
  "profile_url": "https://... or null"}}

Rules:
- name is REQUIRED. Skip items without a plausible human name.
- title: their academic rank / role (Professor, Associate Professor, Lecturer, ...).
- email: only if present on the page; else null. Do not invent.
- profile_url: absolute URL to the person's own profile page if visible, else null.
- Skip administrative staff (unless titled "Professor" / "Lecturer" / "Faculty").
- Do not invent entries. If nothing matches, return [].

PAGE TEXT:
{text}
"""
    res = llm_json(prompt)
    return res if isinstance(res, list) else []

# ---------------- step 4: orchestration ----------------
def load_unis(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            url = row.get("url") or row.get("website")
            if row.get("name") and url:
                rows.append({"name": row["name"].strip(), "url": url.strip()})
    return rows

def main():
    get_client()  # Validate credentials before starting discovery.
    unis = load_unis(UNIS_CSV)
    out  = json.loads(OUT_FILE.read_text()) if OUT_FILE.exists() else {}

    for uni in unis:
        key = uni["name"]
        if key in out and out[key].get("departments"):
            print(f"✓ skip {key} (done)")
            continue

        print(f"\n== {uni['name']} ==")
        depts = discover_departments(uni["name"], uni["url"])
        print(f"  {len(depts)} departments found")

        dept_results = []
        for d in depts:
            fac_url = find_faculty_page(d["url"])
            html    = fetch(fac_url) if fac_url else None
            profs   = extract_professors(html, fac_url, uni["name"], d["name"]) if html else []
            print(f"    • {d['name']}  →  {len(profs)} professors")
            dept_results.append({
                "name":         d["name"],
                "url":          d["url"],
                "faculty_url":  fac_url,
                "professors":   profs,
            })
            time.sleep(1.5)   # stay under OpenRouter 20 rpm

        out[key] = {**uni, "departments": dept_results}
        OUT_FILE.write_text(json.dumps(out, indent=2, ensure_ascii=False))
        print(f"  saved → {OUT_FILE}")

if __name__ == "__main__":
    main()