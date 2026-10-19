# AI-Powered University Discovery System — Python Architecture

## 1. Project Overview

You want to develop a Python application that can **automatically discover universities in any country, collect information from their official websites, and store the results in a structured database.**

For example, the user enters:

```json
{
  "country": "Canada"
}
```

Your application should:

1. Receive a country name, such as Canada, Germany, or the United States.
2. Search the internet for universities located in that country.
3. Discover university names and official websites.
4. Verify that each institution is a legitimate university.
5. Visit university websites and extract relevant information.
6. Identify available academic programs and departments.
7. Store the information in a database.
8. Return a structured JSON response.

Later, you can extend the application to find professors, research opportunities, admission requirements, and scholarships.

**My recommendation is to design the system as a modular university discovery platform with optional AI capabilities.**

You do not need to train an AI model to implement this application.

---

# 2. Does This Project Need AI?

**Short answer: No, not for discovering universities. However, AI becomes valuable when analyzing their websites and extracting complex information.**

Consider three approaches.

| Approach | Technologies | AI Required? | Complexity |
|---|---|---|---|
| Basic university discovery | Python, APIs, requests | No | Low |
| University discovery and web scraping | Python, Scrapy, BeautifulSoup | No | Medium |
| Intelligent university research | Python, LLM, LangChain, RAG | Yes | High |

### Approach 1: Without AI

You can discover universities using existing datasets, search engines, and official government directories.

For example:

```text
Input:
    Canada

        ↓

Search university directories

        ↓

Extract university names

        ↓

Find official university websites

        ↓

Save results in PostgreSQL

        ↓

Return JSON
```

This approach is sufficient if your objective is simply to identify universities.

### Approach 2: With AI

AI becomes useful when you want to understand information published on university websites.

For example, suppose a university publishes the following admission requirements:

> Applicants must hold a four-year bachelor's degree in a relevant discipline and demonstrate English language proficiency. Research-based applicants are encouraged to contact potential supervisors before submitting an application.

An LLM can convert this text into structured information:

```json
{
  "degree_requirement": "Bachelor's degree",
  "degree_duration": "4 years",
  "field_requirement": "Relevant discipline",
  "english_proficiency_required": true,
  "contact_supervisor": "Recommended",
  "program_type": "Research-based"
}
```

You can use an existing LLM through an API, such as an OpenAI model, or run an open-weight model locally.

**You do not need to train or fine-tune your own model initially.**

---

# 3. Recommended Software Architecture

I recommend designing your application around six main components:

1. API Server
2. University Discovery Engine
3. Website Crawler
4. AI Information Extractor
5. Data Validation Engine
6. Database and Search Engine

### High-Level Architecture

```text
                   ┌────────────────────────┐
                   │         USER           │
                   │                        │
                   │ Country: Canada        │
                   │ Degree: Master's       │
                   │ Field: AI (optional)   │
                   └────────────┬───────────┘
                                │
                                ▼
                   ┌────────────────────────┐
                   │      FastAPI Server    │
                   │                        │
                   │ POST /universities     │
                   │ POST /discover         │
                   └────────────┬───────────┘
                                │
                                ▼
                   ┌────────────────────────┐
                   │    Task Manager        │
                   │                        │
                   │ Celery + Redis         │
                   └────────────┬───────────┘
                                │
                                ▼
              ┌─────────────────────────────────┐
              │    UNIVERSITY DISCOVERY ENGINE  │
              │                                 │
              │  Government Directories         │
              │  University Datasets            │
              │  Search Engine APIs             │
              └────────────────┬────────────────┘
                               │
                               ▼
              ┌─────────────────────────────────┐
              │      UNIVERSITY VALIDATION      │
              │                                 │
              │  Remove Duplicates              │
              │  Verify Country                 │
              │  Verify Official Domain         │
              │  Verify Institution Status      │
              └────────────────┬────────────────┘
                               │
                               ▼
              ┌─────────────────────────────────┐
              │          WEB CRAWLER            │
              │                                 │
              │  Scrapy                         │
              │  BeautifulSoup                  │
              │  Playwright                     │
              └────────────────┬────────────────┘
                               │
                               ▼
              ┌─────────────────────────────────┐
              │       AI EXTRACTION ENGINE      │
              │                                 │
              │  LLM                            │
              │  LangChain (optional)           │
              │  Structured JSON Output         │
              └────────────────┬────────────────┘
                               │
                               ▼
              ┌─────────────────────────────────┐
              │       VALIDATION ENGINE         │
              │                                 │
              │  Schema Validation              │
              │  Source Verification            │
              │  Confidence Assessment          │
              └────────────────┬────────────────┘
                               │
                               ▼
              ┌─────────────────────────────────┐
              │           DATABASE              │
              │                                 │
              │  PostgreSQL                     │
              │  Redis                          │
              │  pgvector (optional)            │
              └────────────────┬────────────────┘
                               │
                               ▼
                   ┌────────────────────────┐
                   │       REST API         │
                   │                        │
                   │ Universities           │
                   │ Programs               │
                   │ Professors             │
                   │ Admission Requirements │
                   └────────────────────────┘
```

This architecture supports both a simple university search application and a future AI-powered university matching platform.

---

# 4. How to Find All Universities in a Country

This is the most important part of your project.

**Do not rely exclusively on Google searches or an LLM to generate university names.**

Search engines may omit universities, and LLMs can produce incorrect or outdated names.

Instead, combine several independent sources.

## 4.1 University Discovery Sources

| Source | Purpose | Priority |
|---|---|---|
| Government education directories | Find officially recognized universities | Very High |
| WHED | Discover internationally recognized institutions | Very High |
| Open university datasets | Generate initial university lists | High |
| Wikidata SPARQL | Discover additional institutions and metadata | High |
| Search engine APIs | Find missing universities and websites | Medium |
| LLM | Analyze and classify discovered information | Medium |

### Source 1: Canadian Government Directories

For Canada, an excellent starting point is the Canadian Information Centre for International Credentials (CICIC).

Website:

https://www.cicic.ca/

Its directory includes institutions recognized, authorized, registered, or licensed by provincial and territorial authorities. It supports filtering by institution type and province. [CICDI](https://www.cicdi.ca/868/search_the_directory_of_educational_institutions_in_canada.canada?utm_source=chatgpt.com)

Your application can use this directory as an authoritative reference for verifying Canadian universities.

### Source 2: World Higher Education Database

Website:

https://whed.net/

The World Higher Education Database (WHED) provides information about recognized higher education institutions worldwide.

It includes institutional identifiers, names, locations, websites, and accreditation information. [World Higher Education Database](https://whed.net/About.html?utm_source=chatgpt.com)

**Important:** WHED restricts copying substantial parts of its database without permission. Use its permitted access options or obtain authorization for bulk data collection. [World Higher Education Database](https://whed.net/home.html?utm_source=chatgpt.com)

### Source 3: Wikidata

Website:

https://www.wikidata.org/

Wikidata provides structured information that can be queried using SPARQL.

For example, you can search for institutions categorized as universities in Canada.

Example SPARQL query:

```sparql
SELECT DISTINCT ?university ?universityLabel ?website
WHERE {
  ?university wdt:P31/wdt:P279* wd:Q3918 .
  ?university wdt:P17 wd:Q16 .

  OPTIONAL {
    ?university wdt:P856 ?website .
  }

  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "en".
  }
}
```

This query looks for:

- Entities classified as universities or subclasses of universities.
- Institutions located in Canada.
- Official websites, when available.

Wikidata is useful for discovering candidates, but its classification and coverage are not guaranteed to be complete.

---

# 5. How the University Discovery Engine Works

Suppose your application receives:

```json
{
  "country": "Canada",
  "include_programs": true,
  "include_professors": false
}
```

### Step 1: Normalize the country

Convert the country name into a standard ISO country code.

```python
import pycountry

def get_country_code(country_name):
    country = pycountry.countries.lookup(country_name)
    return country.alpha_2

print(get_country_code("Canada"))
```

Output:

```text
CA
```

### Step 2: Discover universities

Run multiple discovery methods:

```text
                    CANADA
                       |
         ┌─────────────┼─────────────┐
         |             |             |
         ▼             ▼             ▼
      Wikidata      Government     Search API
         |           Directory        |
         ▼             ▼             ▼
     University     University     University
       List A         List B         List C
         |             |             |
         └─────────────┼─────────────┘
                       |
                       ▼
                  Merge Results
                       |
                       ▼
                 Remove Duplicates
                       |
                       ▼
                 Verify Universities
                       |
                       ▼
                   PostgreSQL
```

### Step 3: Remove duplicates

Different sources may return:

```text
University of Toronto
Toronto University
University of Toronto, Canada
```

Your application should determine whether these names refer to the same institution.

You can use:

- Official website domains
- Wikidata IDs
- WHED IDs, where available
- Normalized institution names
- Fuzzy string matching

A library such as `RapidFuzz` can help identify potential duplicates.

However, do not automatically merge institutions solely because their names are similar.

### Step 4: Verify each university

For each university, check:

```json
{
  "name": "University of Toronto",
  "country": "Canada",
  "website": "https://www.utoronto.ca",
  "verified": true,
  "verification_source": "Official directory"
}
```

The `verified` field should only be true when the institution's identity and status have been confirmed through an appropriate source.

A successful HTTP response from a website is not proof of university recognition.

---

# 6. Website Crawler Architecture

Once you discover universities, the next step is visiting their websites.

For example:

```text
University of Toronto
        |
        ▼
https://www.utoronto.ca
        |
        ▼
Website Crawler
        |
        ├── About University
        |
        ├── Faculties
        |
        ├── Departments
        |
        ├── Academic Programs
        |
        ├── Admissions
        |
        ├── Tuition Fees
        |
        └── Research
```

## Recommended Python Libraries

| Library | Purpose |
|---|---|
| `httpx` | Asynchronous HTTP requests |
| `BeautifulSoup4` | Parse HTML |
| `Scrapy` | Large-scale web crawling |
| `Playwright` | Websites requiring JavaScript |
| `trafilatura` | Extract readable text |
| `pypdf` | Extract information from PDFs |
| `Pydantic` | Validate structured data |

I recommend starting with `httpx`, BeautifulSoup, and Trafilatura.

Introduce Scrapy when you need to crawl thousands of pages.

Use Playwright only for websites that require JavaScript rendering.

Your crawler should respect `robots.txt`, website terms, reasonable request rates, and access restrictions.

---

# 7. AI Information Extraction

This is where an LLM becomes useful.

University websites have different structures.

For example:

**University A**

```text
/admissions/graduate/requirements
```

**University B**

```text
/study/postgraduate/how-to-apply
```

**University C**

```text
/future-students/graduate-admissions
```

Traditional scraping requires different selectors for different websites.

An LLM can analyze the extracted text and produce consistent structured output.

## AI Extraction Pipeline

```text
       University Website
               |
               ▼
         HTML Downloader
               |
               ▼
         HTML Text Parser
               |
               ▼
          Text Cleaning
               |
               ▼
          LLM Extraction
               |
               ▼
         Structured JSON
               |
               ▼
        Pydantic Validation
               |
               ▼
       Source Verification
               |
               ▼
           PostgreSQL
```

### Example LLM Input

```text
Extract the following information from this
university admission page:

1. University name
2. Degree level
3. Minimum GPA
4. IELTS requirement
5. TOEFL requirement
6. Application deadline
7. Application fee

Return valid JSON.

Use null for information not found.

Do not invent information.
```

### Expected Output

The following is an illustrative example, not verified admission information:

```json
{
  "university": "Example University",
  "degree": "Master's",
  "minimum_gpa": 3.0,
  "ielts": 6.5,
  "toefl": 90,
  "deadline": "2027-01-15",
  "application_fee": 120,
  "currency": "CAD"
}
```

Every extracted field should ideally include its source URL, retrieval date, and supporting text.

This allows your system to detect errors and verify results.

---

# 8. Database Architecture

I recommend **PostgreSQL** for your primary database.

You should design the database so that additional information can be added later.

### Database Relationships

```text
COUNTRIES
   |
   | 1:N
   ▼
UNIVERSITIES
   |
   ├──────────────┐
   |              |
   ▼              ▼
DEPARTMENTS    ADMISSION_REQUIREMENTS
   |
   ├──────────────┐
   |              |
   ▼              ▼
PROGRAMS       PROFESSORS
                  |
                  ▼
              PUBLICATIONS
```

### Main Database Tables

**universities**

| Column | Type |
|---|---|
| id | UUID |
| name | VARCHAR |
| country_code | VARCHAR |
| province | VARCHAR |
| city | VARCHAR |
| website | VARCHAR |
| institution_type | VARCHAR |
| verified | BOOLEAN |
| last_checked | TIMESTAMP |

**programs**

| Column | Type |
|---|---|
| id | UUID |
| university_id | UUID |
| name | VARCHAR |
| degree_level | VARCHAR |
| department | VARCHAR |
| language | VARCHAR |
| tuition_fee | NUMERIC |
| application_deadline | DATE |

**professors**

| Column | Type |
|---|---|
| id | UUID |
| university_id | UUID |
| name | VARCHAR |
| department | VARCHAR |
| research_interests | TEXT |
| email | VARCHAR |
| profile_url | VARCHAR |

I would also add a `sources` table containing the original URL, retrieval timestamp, source type, and verification status.

This makes the database more reliable and auditable.

---

# 9. Python Project Structure

I recommend the following architecture:

```text
university-discovery/
│
├── app/
│   │
│   ├── main.py
│   │
│   ├── api/
│   │   ├── universities.py
│   │   ├── discovery.py
│   │   └── jobs.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── logging.py
│   │
│   ├── discovery/
│   │   ├── discovery_manager.py
│   │   ├── wikidata.py
│   │   ├── government_sources.py
│   │   ├── search_engine.py
│   │   └── deduplication.py
│   │
│   ├── crawler/
│   │   ├── crawler_manager.py
│   │   ├── html_parser.py
│   │   ├── link_extractor.py
│   │   └── pdf_parser.py
│   │
│   ├── ai/
│   │   ├── llm_client.py
│   │   ├── university_extractor.py
│   │   ├── program_extractor.py
│   │   └── professor_extractor.py
│   │
│   ├── validation/
│   │   ├── university_validator.py
│   │   └── schema_validator.py
│   │
│   ├── database/
│   │   ├── models.py
│   │   ├── connection.py
│   │   └── repository.py
│   │
│   ├── schemas/
│   │   ├── university.py
│   │   └── discovery.py
│   │
│   └── workers/
│       └── discovery_tasks.py
│
├── tests/
│
├── migrations/
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
└── README.md
```

This separates discovery, crawling, AI extraction, validation, and database operations.

---

# 10. REST API Design

Your application can expose several endpoints.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/discover` | Start university discovery |
| GET | `/api/jobs/{id}` | Check discovery progress |
| GET | `/api/universities` | List universities |
| GET | `/api/universities/{id}` | University details |
| GET | `/api/universities/{id}/programs` | Academic programs |
| GET | `/api/universities/{id}/professors` | Professors |
| POST | `/api/universities/{id}/refresh` | Update university information |

### Example Request

```http
POST /api/discover
Content-Type: application/json
```

```json
{
  "country": "Canada",
  "include_programs": false,
  "include_professors": false
}
```

### Example Response

```json
{
  "job_id": "job_123456",
  "country": "Canada",
  "status": "processing",
  "message": "University discovery started"
}
```

Because discovering and verifying universities can take time, the API should return a job ID instead of keeping the HTTP request open.

The client can then query:

```http
GET /api/jobs/job_123456
```

---

# 11. Do You Need RAG or LangChain?

For your first version, **neither RAG nor LangChain is necessary**.

They become useful as the application grows.

### When to Use RAG

Suppose your database contains information from thousands of university websites.

A user asks:

> Find Canadian universities offering research-based master's programs in artificial intelligence with IELTS requirements of 6.5 or lower.

Your system could:

1. Search structured university and program records.
2. Retrieve relevant admission documents.
3. Use vector search to identify related information.
4. Send retrieved content to an LLM.
5. Generate an answer supported by source links.

This is a suitable application of Retrieval-Augmented Generation.

### When to Use LangChain

LangChain can help orchestrate:

- LLM calls
- Document retrieval
- Structured extraction
- Tool usage
- Multi-step research workflows

However, it introduces additional dependencies and complexity.

For the initial version, direct Python functions and an LLM API are sufficient.

---

# 12. Recommended Technology Stack

| Component | Recommended Technology |
|---|---|
| Programming language | Python 3.12+ |
| Backend API | FastAPI |
| HTTP client | HTTPX |
| Web crawler | Scrapy |
| HTML parsing | BeautifulSoup |
| Dynamic websites | Playwright |
| AI model | OpenAI API or local LLM |
| Structured extraction | Pydantic |
| Database | PostgreSQL |
| Vector search | pgvector |
| Task queue | Celery |
| Message broker | Redis |
| Containerization | Docker Compose |
| Testing | pytest |
| Database migrations | Alembic |

For deployment, you could run the API, crawler workers, PostgreSQL, and Redis as separate Docker Compose services.

---

# 13. Development Roadmap

I recommend implementing the project in four phases.

## Phase 1 — University Discovery Without AI

**Goal:** Find universities in a country and save their names and official websites.

Implement:

1. Country name validation.
2. Wikidata integration.
3. Government directory integration.
4. University deduplication.
5. Official website identification.
6. PostgreSQL storage.
7. FastAPI endpoints.

Expected result:

```text
User enters Canada
        ↓
System discovers university candidates
        ↓
System verifies institutions
        ↓
System stores university records
        ↓
User receives university list
```

**This is the MVP I recommend building first.**

A key acceptance test is coverage: compare your results with an authoritative country directory, and report verified, unverified, and missing institutions separately. Do not claim the application found *all* universities unless you have measured completeness against a defined source and institution category.

## Phase 2 — Intelligent Website Crawling

**Goal:** Extract university details from official websites.

Add:

- Department discovery
- Academic program discovery
- Admission page identification
- PDF processing
- Source URL tracking
- Scheduled data refresh

This phase can initially work without AI.

## Phase 3 — AI-Powered Extraction

**Goal:** Automatically understand admission requirements and research information.

Add:

- LLM integration
- Structured JSON extraction
- Program classification
- Research field identification
- Professor profile extraction
- Validation against source documents

At this stage, AI provides significant value.

## Phase 4 — AI University Matching

This phase connects directly to your broader university matching application.

The user uploads:

```text
Resume.pdf
SOP.pdf
Academic_Transcript.pdf
```

The system extracts the applicant's profile and compares it with universities, programs, and professors.

```text
             USER DOCUMENTS
                   |
                   ▼
            Profile Extraction
                   |
                   ▼
          Applicant Information
                   |
                   ▼
             Matching Engine
                   |
       ┌───────────┼───────────┐
       |           |           |
       ▼           ▼           ▼
   Universities  Programs   Professors
       |           |           |
       └───────────┼───────────┘
                   |
                   ▼
              AI Ranking
                   |
                   ▼
          Recommended Matches
```

A matching result might contain:

```json
{
  "university": "Example University",
  "program": "MSc Computer Science",
  "research_area": "Computer Vision",
  "professor": "Example Professor",
  "match_score": 87,
  "matched_skills": [
    "Python",
    "Computer Vision",
    "Deep Learning",
    "Embedded AI"
  ],
  "admission_eligibility": "Needs verification"
}
```

The match score would be produced by your own scoring algorithm, not represent an official admission probability.

---

# 14. Final Architecture Recommendation

For your project, I recommend starting with this simplified architecture:

```text
                FastAPI
                   |
                   ▼
          Discovery Manager
                   |
         ┌─────────┴─────────┐
         |                   |
         ▼                   ▼
      Wikidata        Official Directories
         |                   |
         └─────────┬─────────┘
                   |
                   ▼
             Deduplication
                   |
                   ▼
               Validation
                   |
                   ▼
              PostgreSQL
                   |
                   ▼
              REST API
```

Once this works reliably, extend it:

```text
              PostgreSQL
                   |
                   ▼
             Web Crawler
                   |
                   ▼
            Text Extraction
                   |
                   ▼
                 LLM
                   |
                   ▼
           Structured Data
                   |
                   ▼
            Source Validation
                   |
                   ▼
              PostgreSQL
```

### What I Would Build First

Start with a Python application that accepts a country name and returns a verified university list containing:

```json
{
  "country": "Canada",
  "universities": [
    {
      "name": "University of Toronto",
      "website": "https://www.utoronto.ca",
      "city": "Toronto",
      "province": "Ontario",
      "verified": true
    },
    {
      "name": "University of British Columbia",
      "website": "https://www.ubc.ca",
      "city": "Vancouver",
      "province": "British Columbia",
      "verified": true
    }
  ]
}
```

This is an example of the intended output format, not the result of a completed discovery run.

**The most important engineering decision is to separate university discovery from AI analysis.** University discovery should rely on authoritative sources and deterministic validation. AI should be responsible for interpreting unstructured information, not deciding which universities exist.

This will give you a reliable foundation for the larger AI-powered university and professor matching application.
