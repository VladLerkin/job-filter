# Release Notes

## v1.2.4
**Release Date:** November 8, 2026

### Features & Geo-Filtering
- **Foreign On-site / Hybrid Filter:** Integrated `is_remote` tracking into `score_vacancy_by_skill` and `classify_geo_tier`. Jobs requiring physical presence or hybrid office attendance in another country (e.g. `is_remote == 0`, `Télétravail à hauteur de 50%`, `locaux à Lyon`, `X days in office`) without relocation assistance are now strictly rejected (`Rejected: On-site / Hybrid in <Location>` or `<Country>-only`).
- **France Country Lock:** Added France (`france`) and major French cities (`Paris`, `Lyon`, `Villeurbanne`, `Marseille`, `Toulouse`, `Bordeaux`, `Lille`, `Nice`, `Nantes`, etc.) to `FOREIGN_COUNTRY_MAP`, resolving an issue where French remote positions were not recognized by country pool locks.
- **Expanded Country Dictionary:** Added `Sri Lanka`, `Tunisia`, `Tanzania`, `Morocco`, `Serbia` (`Belgrade`, `Novi Sad`), `Montenegro`, and `Monaco` to foreign location mappings.
- **Pipeline `is_remote` Integration:** Passed `is_remote` from database rows into AI enrichment scoring and skills service rescoring pipelines.

### Testing & Maintenance
- **Extended Test Suite:** Added unit tests covering France country lock, foreign hybrid/on-site requirements without relocation (rejected), and foreign hybrid roles with relocation (59 tests passing).

## v1.2.3
**Release Date:** November 8, 2026

### Features & Geo-Filtering
- **Country Pool Restrictions (`country_pool_lock`):** Added detection for multi-country closed remote lists (e.g. `Czech Republic, Slovakia, Hungary` or `Poland, Romania`). Vacancies with foreign country pools excluding the candidate's base location (`Georgia`) without visa sponsorship are now strictly rejected (`Rejected: Restricted countries (...)`).
- **Broad EMEA Disambiguation:** Fixed an issue where localized European country lists formatted as `europe (Country1, Country2, ...)` falsely triggered `Tier 2A: Broad EMEA / Compatible Timezone`, bypassing country-level checks.
- **Temporary WFA Perks vs. Global Remote:** Differentiated internal employee travel perks (e.g. *"Work From Anywhere up to 90 days/year"* or *"can work from anywhere across Japan"*) from true global remote hiring. Explicit country restrictions in `location_restrictions` now prevent false assignment of `Tier 1B: True Global Remote`.
- **Regulatory EU/EEA-Only Lock:** Explicitly reject `EU-only` / `EEA-only` restrictions when relocation assistance is absent.

### Language Filtering & AI Schema
- **Mandatory Foreign Languages Filter:** Expanded mandatory language restrictions to include Portuguese, Japanese, Chinese, Swedish, and others. Vacancies requiring fluent/business proficiency in languages not supported by the candidate's profile are immediately rejected (`Rejected: Language (...)`) prior to relocation assignment.
- **Structured LLM Geo-Eligibility (`candidate_geo_eligibility`):** Added a tri-state field (`"yes" | "no" | "unclear"`) to `JobEnrichment` schema and updated system prompt to `role-tech-resume-v4`, enabling direct LLM verdicts on geographic eligibility against candidate preferences.

### Testing & Maintenance
- **Extended Test Suite:** Added unit tests in `test_scorer.py` covering multi-country remote pools, travel WFA perks, localized WFA phrases, and EU-only restrictions (56 tests passing).

## v1.2.2
**Release Date:** November 7, 2026

### Integrations & Scraping
- **Hirify Strict Time Cutoff (`hours_old`):** Fixed an issue where vacancies were not filtered by time because compact cards from Hirify API lacked timestamp fields. The adapter now parses the true publication date (`created_at` / `published_at`) from vacancy details and strictly cuts off vacancies older than the specified `hours_old` threshold (e.g. 4 hours).
- **Accurate Posting Dates:** Vacancies from Hirify now record their actual creation date in `date_posted` rather than defaulting to today's date.
- **API Quota & Performance Optimization (`processed_ids`):** Hirify cards whose IDs already exist in the local database (`processed_jobs`) are now skipped immediately before calling `read_vacancy`, saving daily API opens quota and speeding up feed collection.

### UI & Usability
- **Persistent Pipeline Log Toggle:** Added an always-visible `Show Log` / `Hide Log` toggle button to the main control toolbar, preventing logs from becoming unopenable after being hidden.
- **Real-Time Pipeline Status Dot:** Added a color-coded status indicator next to the log button (pulsing blue/indigo when running, green when finished with logs, grey when idle).
- **Log Management Controls:** Added a dedicated `Clear` (🧹) button inside the log modal and enhanced collapsible container styling.
- **Pipeline Recovery on Page Load:** Automatic detection of running background pipelines on page reload so log streaming and status resume smoothly without needing a restart.

### Testing & Maintenance
- **Extended Test Suite:** Added unit tests verifying Hirify detail-level date filtering, `processed_ids` skipping, and date accuracy (50 tests passing).

## v1.2.1
**Release Date:** November 6, 2026

### Scraping & Rate-Limiting Protections
- **LinkedIn Rate-Limit Protections (Anti-429):**
  - Increased pause between consecutive LinkedIn search terms from 2–4s to `12.0–20.0s` with live countdown logs, allowing LinkedIn's rate-limiting window to cool down between 50-vacancy queries.
  - Increased internal page-to-page delay in `JobSpy` from `(3, 7)` to `(5, 9)` seconds.
  - Increased card detail fetching delay to `(2.0, 3.5)` seconds with an expanded exponential backoff on HTTP 429 (`attempt * 6.0s + (3..6s)`).

### AI Processing Scale
- **Increased AI Batch Limit to 50:** Raised the default AI processing limit (`llm_limit`) from 15 to 50 across the web UI (`AI Limit` input), API schemas (`RunPipelineRequest`), and backend pipeline runner services (`enrich_and_score_pending_jobs` and `run_pipeline`), matching the increased 50-vacancy feed and scraping scale.

### Bug Fixes & Reliability
- **LLM Enrichment SQL Column Fix:** Resolved `IndexError: No item with that key` by adding `location` to the `SELECT` query in `jobs_repo.list_pending_enrichment` and adding safe dictionary access in `pipeline.py`.

## v1.2.0
**Release Date:** November 6, 2026

### Features & Granular Scoring
- **Granular Score Tiers & Tabs:** Replaced the ambiguous combined "Actionable" tab with granular, focused score categories: `Top Match ≥70` (🟢), `Good 60–69` (🟡), and `Fair 50–59` (🟠). Added corresponding `.badge-fair` styling and color-coded score visual indicators. Retained full backward compatibility for `actionable` query requests in backend services and API endpoints.
- **Increased Location Weighting:** Significantly boosted points for candidate-accessible locations in the scoring model:
  - `Tier 1A` (Local Georgia / Tbilisi): boosted from +20 to +35 points.
  - `Tier 1B` (True Global Remote / Worldwide): boosted from +18 to +30 points.
  - `Tier 2A` (Broad EMEA / Timezone): adjusted to +18 points (from +12).
  - `Tier 2B` (Relocation / Sponsorship): maintained at +10 points.
  Ensures jobs legally and practically workable from Georgia rank prominently in top tiers.
- **Dismissed Tab Breakdown & Feed Restoration:** Split the `Dismissed` (`Отсеянные`) tab into interactive sub-filters: `All Dismissed`, `👤 Dismissed by Me` (`rejection_source = 'user'`), and `🤖 Filtered by Auto/AI` (`rejection_source = 'auto'`). Added dynamic breakdown chips for 1-click filtering by user rejection reasons or auto-filter categories, plus a 1-click `↩ Restore to Feed` button for auto-rejected vacancies (`user_status = 'saved'`).

### Integrations & Scraping
- **Hirify Feeds Scale & Limits:** Increased maximum vacancy limit per saved filter / feed from 25 to 50 across the Hirify scraping adapter, pipeline services, and UI trigger.

### Geo Disambiguation & Bug Fixes
- **US vs. Georgia Country Disambiguation:** Fixed US state Georgia vs. country Georgia confusion (US city/state combinations like "San Ramon, CA", "usa", and 401(k) benefits now trigger `us_only_lock` instead of false Tier 1A match).
- **LLM Commentary Isolation:** Excluded LLM work authorization analysis text from positive location matching to prevent negative phrases (e.g., "ineligible for candidate in Georgia") from triggering false positive matches.
- **Single-Country Locks:** Added explicit single-country locks for Mexico, Argentina, India, and Brazil.
- **Rescoring Engine Fixes:** Fixed `AttributeError: 'tuple' object has no attribute 'keys'` in `candidate_repo.get_settings` when reading SQLite row tuples, and updated `jobs_repo.update_enrichment_and_score` to clear stale rejection reasons upon rescore.

### Testing & Maintenance
- **Extended Test Suite:** Added unit and integration tests covering granular tabs, score distribution stats, geo-classification, and feed limits (49 tests passing).

## v1.1.1
**Release Date:** November 6, 2026

### Blacklist & ATS Platform Safety
- **Search Aggregators Protection:** Protected core search aggregators (`linkedin.com`, `hirify.me`, `indeed.com`, `glassdoor.com`) from being blacklisted. API endpoints, background services, and the web UI now strictly reject aggregator blacklisting attempts, ensuring continuous search pipeline functionality.
- **Captcha & Anti-Bot Service Filtering:** Added automatic filtering for bot-protection and utility domains (`hcaptcha.com`, `recaptcha.net`, `challenges.cloudflare.com`, `arkoselabs.com`, `geetest.com`). Service iframes are no longer mistaken for career ATS boards.
- **Database Cleanup:** Purged errant utility and aggregator entries (`hcaptcha.com`, `indeed.com`) from `blacklisted_boards`, repairing associated vacancies (such as HashOptima on Lever) back to actionable status.

### UI & Modal Enhancements
- **Dynamic Domain Extraction in Blacklist Modal:** Replaced the hardcoded `'cims.com'` fallback with dynamic domain parsing from `job.apply_url` and `job.url`. Vacancies without a third-party ATS now open with an empty domain input for company-level blocking.
- **Quick Platform Chips:** Added 1-click chips for `lever.co` and `greenhouse.io` alongside Workday, Taleo, and iCIMS.

### Testing & Maintenance
- **Extended Test Suite:** Added unit and integration tests covering aggregator domain protection and API validation (45 tests passing).

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

