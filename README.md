# 🎯 Job Filter

> **AI-Powered Automated Vacancy Discovery, Multi-Board Scraping, LLM Enrichment & Weighted Candidate Scoring Engine.**

**Job Filter** is an intelligent assistant and dashboard designed for senior software engineers, backend specialists, and Agentic AI practitioners. It automates job hunting across major platforms (LinkedIn, Indeed, Glassdoor), filters out inaccessible ATS applications, enriches job postings using Gemini LLMs, and computes personalized match scores based on a customizable **Skills Matrix**.

---

## ⚡ Core Features

- 🌐 **Multi-Board Scraping**: Aggregates job vacancies from verified platforms: LinkedIn, Indeed, and Glassdoor using `python-jobspy` across targeted locations (`Remote`, `EMEA`, `Worldwide`).
- 🤖 **LLM Vacancy Enrichment**: Analyzes job descriptions via `agy` CLI (e.g. `gemini-3.8-flash-low`, `gemini-4-argon`, `claude-sonnet-5-5`) to extract:
  - **Geographic Eligibility**: Classifies positions as `GLOBAL`, `RESTRICTED_US`, or `RESTRICTED_EU`.
  - **Technology Stack**: Extracts required languages, frameworks, and architecture patterns.
  - **Agentic AI Classification**: Detects whether a job involves autonomous AI agents, LangGraph, LLM orchestration, RAG, or MCP.
  - **Company Red Flags & Compensation**: Identifies equity-only offers, hidden requirements, and salary ranges.
- ⚖️ **Weighted Candidate Scoring**: Automatically scores each job from `0` to `100` against your personalized skills matrix, applying category multipliers and penalty deductions for non-target tech stacks.
- 📄 **Smart PDF Resume (CV) Ingestion**:
  - Automatically parses PDF resumes using `pypdf`.
  - Generates a polished, global-standard Markdown CV and candidate summary.
  - Computes years of experience per technical skill and maps skills to standard categories.
  - Features an **interactive diff modal** with category dropdowns (`<select>`) and experience adjustments before committing to the database.
- 🚫 **1-Click ATS Blacklist Management**: Block problematic ATS application portals or specific employers with one click.
- 🌐 **Bilingual Interface (EN / RU)**: Seamless one-click language toggle between English and Russian in the top header.
- 💻 **Modern Web Dashboard**: Fast, responsive Single Page Application (SPA) with a sleek dark theme built with Tailwind CSS.

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

### Option 1: macOS One-Click Launcher (Recommended)
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
To scrape vacancies, enrich them with AI, and score them directly in the terminal:
```bash
source .venv/bin/activate
python -m job_filter
```

---

## 🏁 Getting Started: Recommended Workflow

To get the most accurate, personalized job matching, follow these steps when using Job Filter for the first time:

### Step 1: Upload Your Resume (PDF)
1. Open the dashboard at `http://localhost:8000`.
2. In the top-right header (or under Profile tab), click **«📄 Upload PDF Resume»**.
3. Select your latest resume file (`.pdf`).
4. The AI will:
   - Extract and normalize your resume into clean Markdown.
   - Generate a concise candidate profile summary.
   - Calculate years of experience for every technical skill.
   - Automatically assign skills to appropriate categories (`🤖 AI & Agentic Systems`, `☕ Core Backend`, `🐍 Secondary Languages`, `🏗️ Architecture & DevOps`, `💼 Business Domains`).

### Step 2: Review & Apply Skills in the Diff Modal
1. An interactive **Diff Modal** will appear displaying newly discovered and modified skills.
2. For each skill, you can:
   - Change the assigned category using the **interactive `<select>` dropdown** (scores update dynamically).
   - Adjust the calculated **years of experience**.
   - Review and edit synonyms/aliases.
3. Check **«🔄 Rescore all vacancies immediately»** and click **«✅ Apply Selected Changes»**.

### Step 3: Configure Your Search
1. In the search panel, select your target roles (e.g. `Agentic Engineer Remote`, `AI Agent Engineer Remote`, `Software Engineer Remote`).
2. Choose job platforms (LinkedIn, Indeed, Glassdoor) and target region (e.g. `Remote`, `EMEA`, `Worldwide`).
3. Set the results limit and hours freshness filter.

### Step 4: Run Discovery & Review Matches
1. Click **«🚀 Search + AI Filter»** (or **«🧠 AI Only»** to re-analyze existing vacancies).
2. Monitor real-time status in the header (`Scraping` $\to$ `Enriching` $\to$ `Idle`).
3. Use quick filters to focus on high-yield opportunities:
   - **🔥 TOP (70+)**: Best match for your stack and experience.
   - **⚡ GOOD (50-69)**: Solid match with minor skill gaps.
4. Click **«🔗 Open Vacancy»** to view the posting.
5. If an ATS portal requires tedious multi-page account creation or is inaccessible, click **«⛔ Blacklist»** to permanently hide it and all future jobs from that domain or employer.

---

## 🧪 Running Tests

The automated test suite covers API endpoints, repository queries, scoring rules, geo tiers, CV diffing, and URL normalizers:

```bash
# Run all tests
pytest -v

# Run only scoring tests
pytest tests/test_scorer.py -v

# Run CV diff & category tests
pytest tests/test_skills_diff.py -v
```

---

## 📖 Architecture & Deep Dive

For detailed system design, folder structure, sequence diagrams, scoring formulas, and environment configuration:
- 📘 [System Design & Architecture Document](docs/design.md)
