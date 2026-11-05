# Release Notes

## v1.1.0
**Release Date:** November 5, 2026

### Features & Architecture
- **Graduated Remote Geo-Scoring:** Added configurable candidate geo-preferences (`home_region`, `home_country`, `relocation_policy`, `eligible_regions`, `restricted_regions`) injected dynamically into LLM enrichment prompts. Global remote vacancies and vacancies permitting work from the candidate's home region (e.g., Caucasus / Georgia / EMEA) receive top suitability scores, while roles restricted to specific third countries without relocation support are filtered out or scored low.
- **Structured Vacancy Dismissal ("Не подошла"):** Added a formal rejection workflow allowing users to mark vacancies as not suitable and specify standardized reasons (location/citizenship restrictions, tech stack mismatch, seniority level, compensation/terms, company domain). Both `user_status = 'rejected'` and `user_reject_reason` are persisted in SQLite, instantly moving disqualified jobs out of active tabs into `Отсеянные`.
- **AI Training & Feedback Dataset:** Introduced `GET /api/jobs/user-rejections` endpoint to retrieve user-disqualified vacancies with full context (title, company, description, extracted skills, and explicit rejection reasons) for continuous AI prompt tuning and negative rule calibration.

### UI & Usability
- **Interactive Rejection Modal:** Added a responsive dialog with 1-click quick-select reason chips and free-form note inputs.
- **Dismissal Reason Badges:** Visual indicators and reason tags on cards in the Rejected tab, complete with 1-click options to edit the reason or restore the vacancy back to `new`.
- **Candidate Geo-Preferences Integration:** Enhanced candidate profile settings to support customized regional constraints and relocation policies without hardcoding prompt logic.

### Testing & Maintenance
- **Expanded Test Suite:** Added end-to-end repository and API tests covering rejection workflows, tab isolation, and dataset extraction (43 tests passing).

## v1.0.0
**Release Date:** November 2, 2026

### Features & Architecture
- **Multi-Board Scraping Engine:** Integrated high-reliability scraping across verified job aggregators: LinkedIn, Indeed, Glassdoor, and the Hirify Agent REST API with region and freshness filtering.
- **Hirify Saved Feeds Mode:** Added first-class support for Hirify Saved Searches (Feeds), allowing users to fetch vacancies directly using their pre-configured account filters (`AI Agentic Engineer`, `Remote Global`) without manual keyword entry, complete with real-time pipeline logs and deduplication.
- **Skills Matrix & Multiplier Scoring:** Implemented an intelligent scoring system tailored for senior backend and AI/Agentic engineers. Features category-level multipliers, point caps, penalty deductions, and instant vacancy rescoring upon matrix changes.
- **AI-Powered CV Parsing & Interactive Diff Modal:** Built PDF resume ingestion via Gemini LLM prompts, estimating years of experience per skill, mapping skills to weighted categories, and presenting an interactive diff modal before committing changes to SQLite.
- **Gemini LLM Enrichment via `agy` CLI:** Automated deep vacancy analysis extracting Agentic AI tier classification, geographic eligibility (US-only vs. Global Remote), tech stack breakdown, and compensation details.
- **ATS Blacklist & Domain Tracking:** Automatic URL normalization, detection of applicant tracking systems (Workday, Greenhouse, Lever, Ashby, iCIMS, SmartRecruiters), and domain blacklist rules.
- **Modern Responsive Dashboard:** Single-page dashboard built with Tailwind CSS, status tabs (`Actionable`, `Top Match ≥70`, `Good 50–69`, `Pending AI`, `Applied`, `Dismissed`), and instant EN/RU language switching.

