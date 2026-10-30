# 🎯 Job Filter

> **AI-Powered Automated Vacancy Discovery, Multi-Board Scraping, LLM Enrichment & Weighted Candidate Scoring Engine.**

**Job Filter** is an intelligent assistant and dashboard designed for senior software engineers, backend specialists, and Agentic AI practitioners. It automates job hunting across major platforms (LinkedIn, Indeed, Glassdoor, ZipRecruiter), filters out inaccessible ATS applications, enriches job postings using Gemini LLMs, and computes personalized match scores based on a customizable **Skills Matrix**.

---

## ⚡ Core Features

- 🌐 **Multi-Board Scraping**: Aggregates job vacancies from LinkedIn, Indeed, Glassdoor, and ZipRecruiter using `python-jobspy` across targeted locations (`Remote`, `EMEA`, `Worldwide`).
- 🤖 **LLM Vacancy Enrichment**: Analyzes job descriptions via `agy` CLI (e.g. `gemini-3.8-flash-low`, `gemini-4-argon`, `claude-sonnet-5-5`) to extract:
  - **Geographic Eligibility**: Classifies positions as `GLOBAL`, `RESTRICTED_US`, or `RESTRICTED_EU`.
  - **Technology Stack**: Extracts required languages, frameworks, and architecture patterns.
  - **Agentic AI Classification**: Detects whether a job involves autonomous AI agents, LangGraph, LLM orchestration, RAG, or MCP.
  - **Company Red Flags & Compensation**: Identifies equity-only offers, hidden requirements, and salary ranges.
- ⚖️ **Weighted Scoring Matrix**: Scores each job from `0` to `100`:
  - Category-level multipliers and point caps (e.g., Agentic AI up to 30 pts, Backend up to 20 pts).
  - Negative penalty deductions for non-target tech stacks (e.g., Golang, .NET, Rust, PHP) and legacy technologies (1C, SAP).
  - Geographic caps penalizing US-only restricted roles.
- 📄 **Smart PDF Resume (CV) Ingestion**:
  - Automatically parses PDF resumes using `pypdf`.
  - Generates a polished, global-standard Markdown CV and candidate summary.
  - Computes years of experience per technical skill and maps skills to standard categories.
  - Features an **interactive diff modal** with category dropdowns (`<select>`) and experience adjustments before committing to the database.
  - Automatically provisions new categories in SQLite using official defaults.
- 🚫 **1-Click ATS Blacklist Management**: Block problematic application portals (e.g., iCIMS, Taleo, Brassring) or specific employers with one click.
- 💻 **Modern Web Dashboard**: Fast, responsive Single Page Application (SPA) with a sleek dark theme built with Tailwind CSS.

---

## 🏗️ Architecture & Project Structure

Job Filter follows a clean, modular **layered architecture**:

```
job-filter/
├── app.py                      # Uvicorn entrypoint for web server
├── start_app.command           # macOS one-click launcher (starts server + opens browser)
├── requirements.txt            # Production runtime dependencies
├── requirements-dev.txt        # Development dependencies (pytest, etc.)
├── jobs.db                     # SQLite database file (WAL mode)
│
├── job_filter/                 # Core modular Python package
│   ├── config.py               # Centralized configuration & environment variables
│   ├── logging_setup.py        # Rotating file & console logging setup
│   │
│   ├── api/                    # FastAPI routes, dependencies, and request schemas
│   │   ├── app.py              # Application factory & middleware configuration
│   │   ├── deps.py             # Database session dependency injection
│   │   ├── schemas.py          # Pydantic request models
│   │   └── routers/            # Domain-based routers (candidate, jobs, pipeline, skills, system)
│   │
│   ├── db/                     # Database engine & migrations
│   │   ├── connection.py       # SQLite connection manager & WAL pragmas
│   │   ├── schema.py           # DDL schema definition & soft migrations
│   │   └── seed_data.py        # Default categories, skills matrix & ATS blacklist
│   │
│   ├── llm/                    # Large Language Model integrations
│   │   ├── agy_client.py       # Subprocess wrapper for `agy` CLI with JSON parser
│   │   ├── cv_analyzer.py      # PDF resume analyzer & skill extractor
│   │   └── enricher.py         # Vacancy enrichment prompt & parser
│   │
│   ├── models/                 # Shared domain data models (Pydantic / dataclasses)
│   ├── repositories/           # Direct SQL operations (jobs, skills, candidate, blacklist)
│   ├── scoring/                # Deterministic scoring algorithm & matrix cache
│   ├── scraping/               # Multi-platform scraping (JobSpy) & URL normalizer
│   └── services/               # Workflows (pipeline, CV processing, skills management)
│
├── static/                     # Web dashboard frontend (HTML, Tailwind CSS, JS)
│   ├── index.html              # Dashboard layout
│   ├── css/style.css           # Styling & animations
│   └── js/app.js               # Reactive frontend logic & modals
│
├── tests/                      # Automated test suite (28 passing tests via pytest)
└── docs/                       # System design & documentation
    └── design.md               # Detailed architecture & design specifications
```

For comprehensive architectural details, consult [docs/design.md](docs/design.md).

---

## 📋 Prerequisites

- **Python**: `3.11` or newer.
- **Antigravity CLI (`agy`)**: Used for LLM processing (supports `gemini-3.8-flash`, `gemini-4-argon`, `claude-sonnet-5-5`, etc.). Run `agy models` to view available models.
- **SQLite3**: Built into Python standard library.

---

## 🚀 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <repository_url>
   cd job-filter
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Verify installation by running tests**:
   ```bash
   pytest -v
   ```

---

## 🖥️ How to Run

### Option 1: macOS One-Click Launcher (Recommended for Desktop)
Double-click `start_app.command` in Finder or run:
```bash
./start_app.command
```
This script boots the Uvicorn web server and automatically opens `http://localhost:8000` in your default browser.

### Option 2: Run the Web Server via Uvicorn
```bash
source .venv/bin/activate
uvicorn app:app --reload --port 8000
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

### Option 3: Run the Pipeline via CLI
To scrape vacancies, enrich them with AI, and score them without launching the web server:
```bash
source .venv/bin/activate
python -m job_filter
```
Output will display top-matched vacancies (Score $\ge 50$) with match tiers, scores, and application URLs directly in the terminal.

---

## ⚙️ Configuration & Environment Variables

Job Filter works out-of-the-box with sensible defaults, but can be configured via environment variables:

| Variable | Default Value | Description |
|---|---|---|
| `JOB_FILTER_DB_PATH` | `jobs.db` | Absolute or relative path to the SQLite database |
| `JOB_FILTER_MODEL` | `gemini-3.8-flash-low` | Default LLM model used by `agy` CLI (run `agy models` for options) |
| `JOB_FILTER_LLM_TIMEOUT` | `120` | Timeout in seconds for vacancy enrichment |
| `JOB_FILTER_CV_TIMEOUT` | `180` | Timeout in seconds for CV PDF analysis |
| `JOB_FILTER_PORT` | `8000` | HTTP port for the web dashboard |
| `JOB_FILTER_HOST` | `0.0.0.0` | Bind host for the web server |

---

## 📊 Scoring & Skills Matrix

The scoring engine compares extracted vacancy requirements against the candidate's active skills:

$$\text{FinalScore} = \text{clamp}\left(\sum_{c \in \text{Categories}} \min(P_c, \text{Cap}_c) - \sum_{k \in \text{Penalties}} \text{Penalty}_k - \text{GeoAdjustment}, 0, 100\right)$$

### Default Skill Categories:
1. **🤖 AI & Agentic Systems** (`ai_agentic`): Multiplier **15.0x**, Max Cap **30 pts**  
   *LangGraph, AI Agents, Multi-Agent Architecture, RAG, Vector DB, MCP, LLM Observability.*
2. **☕ Core Backend & Languages** (`core_backend`): Multiplier **2.0x**, Max Cap **20 pts**  
   *Java, Kotlin, Spring Boot, Ktor.*
3. **🐍 Secondary Languages / TS** (`secondary_backend`): Multiplier **3.0x**, Max Cap **18 pts**  
   *Python, TypeScript, Node.js.*
4. **🏗️ Architecture & Cloud / DevOps** (`arch_infra`): Multiplier **2.0x**, Max Cap **15 pts**  
   *Kafka, Microservices, PostgreSQL, Docker, Kubernetes, AWS.*
5. **💼 Business Domains** (`domains`): Multiplier **2.0x**, Max Cap **10 pts**  
   *FinTech, Banking, Payments, Trading.*
6. **🚫 Alien Stack** (`alien`): Multiplier **-1.0x**, Penalty **-20 pts**  
   *Golang, C#, .NET, C++, Rust, Ruby, PHP.*
7. **🦖 Legacy Stack** (`legacy`): Multiplier **-1.0x**, Penalty **-30 pts**  
   *1C Enterprise, SAP/ABAP, Cobol, Salesforce.*

*Note: You can fully customize category titles, multipliers, and caps directly in the web dashboard via the **Skills Matrix** editor.*

---

## 🧪 Running Tests

The test suite covers API endpoints, repository queries, scoring rules, geo tiers, CV diffing, and URL normalizers:

```bash
# Run all tests
pytest -v

# Run only scoring tests
pytest tests/test_scorer.py -v

# Run CV diff & category tests
pytest tests/test_skills_diff.py -v
```

---

## 📖 Documentation

Detailed architectural blueprints, subsystem interaction diagrams, and database entity relationships are documented in:
- [System Design & Architecture Document](docs/design.md)

