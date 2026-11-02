# Release Notes

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

