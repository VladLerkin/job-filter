# Architecture Decision Log (ADR)

This document records the architecturally significant decisions made for **Job Filter**. It focuses exclusively on decisions involving structural trade-offs, layer boundaries, concurrency models, data access patterns, and external integration constraints.

---

## ADR-001: SQLite Transaction Boundaries at the Unit-of-Work Level (`get_db` / `db_session`)

- **Status:** Accepted
- **Context:** The project uses raw `sqlite3` without an ORM. Scattering `conn.commit()` calls across individual repository or service methods makes it impossible to guarantee atomicity for multi-step operations (e.g., updating the candidate profile and recalculating the skills matrix in a single workflow). Furthermore, omitting a `commit()` call causes `sqlite3` to silently roll back uncommitted writes when `conn.close()` is invoked.
- **Considered Alternatives:**
  1. *Autocommit mode (`isolation_level = None`)* — sacrifices atomicity across multi-step operations such as `apply_cv_analysis`.
  2. *Manual `conn.commit()` inside every repository method* — risks partial commits when an exception occurs mid-workflow and is prone to human error.
  3. *Unit-of-Work pattern at the request/session boundary (`get_db` and `db_session`)* — opens a transaction on entry, automatically commits on clean exit, and rolls back (`conn.rollback()`) on any unhandled exception.
- **Decision:** Manage transactions centrally in [`get_db()`](file:///Users/vlad/IdeaProjects/job-filter/job_filter/api/deps.py#L8-L18) for HTTP requests and [`db_session()`](file:///Users/vlad/IdeaProjects/job-filter/job_filter/db/connection.py#L34-L45) for CLI and background tasks. Long-running background workflows ([`pipeline.py`](file:///Users/vlad/IdeaProjects/job-filter/job_filter/services/pipeline.py)) additionally commit intermediate checkpoints after each enriched vacancy.
- **Consequences:** All HTTP handlers are atomic by default; repositories remain pure SQL adapters that can be freely composed within a single transaction.

---

## ADR-002: CORS / Private Network Access (PNA) Policy for `job-auto-applier` Extension Integration

- **Status:** Accepted
- **Context:** The local server (`localhost:8000`) is accessed not only by its own web dashboard, but also by the `job-auto-applier` browser extension content script, which executes inside arbitrary external employer websites and ATS platforms (`*.myworkdayjobs.com`, `*.icims.com`, custom corporate domains) after redirects from job boards.
- **Considered Alternatives:**
  1. *Restrict the API with a static `allow_origins` whitelist* — breaks the browser extension whenever a candidate is redirected to an unknown employer or ATS domain.
  2. *Retain `allow_origins=["*"]` + `Access-Control-Allow-Private-Network: true`, while enforcing strict idempotency (Read-Only) on GET check endpoints* — preserves extension functionality across all external domains while preventing unintended database mutations during background GET requests.
- **Decision:** Keep PNA/CORS open in [`app.py`](file:///Users/vlad/IdeaProjects/job-filter/job_filter/api/app.py#L26-L45) to support cross-origin requests from any external ATS, and set `auto_link=False` by default on [`GET /api/blacklist/check`](file:///Users/vlad/IdeaProjects/job-filter/job_filter/api/routers/blacklist.py#L16-L20) so URL checks have zero database write side effects.
- **Consequences:** The browser extension can seamlessly verify any domain in real time without risking accidental `company_ats_map` overwrites from browser link prefetching.

---

## ADR-003: Two-Stage Geographic Filtering (Flat LLM Schema + Backward-Compatible Deterministic Classifier)

- **Status:** Accepted
- **Context:** Invoking the LLM via the `agy` CLI takes 30–60 seconds per vacancy and has a strict constraint: nested JSON schemas (`$defs`) cause CLI hangs or malformed JSON outputs. With roughly 1,000 enriched vacancies stored in `jobs.db`, evolving geographic or remote filtering rules (e.g., closed multi-country pools, foreign hybrid/on-site offices, regular business travel) must apply to the entire database instantaneously without requiring a 10-hour LLM re-enrichment run.
- **Considered Alternatives:**
  1. *Delegate geo eligibility decisions entirely to the LLM using a deeply nested `GeoFacts` schema* — triggers `agy` CLI hangs on `$defs` and requires re-running the LLM across all historical vacancies whenever candidate preferences change.
  2. *Flat [`JobEnrichment`](file:///Users/vlad/IdeaProjects/job-filter/job_filter/models/enrichment.py) contract + deterministic [`classify_geo_tier`](file:///Users/vlad/IdeaProjects/job-filter/job_filter/scoring/geo.py) classifier with text fallback* — the LLM extracts atomic facts into flat fields (`location_restrictions`, `remote_policy_detail`, `work_arrangement`, `candidate_geo_eligibility`, `required_languages`, `requirements`), while deterministic Python logic in `geo.py` computes the final eligibility and tier (`Tier 1A..3`).
- **Decision:** Adopt Alternative 2. Whenever new fields are added to `JobEnrichment` (such as `work_arrangement`), `classify_geo_tier` in `geo.py` retains fallback parsing over raw text fields (`remote_policy_detail`, `requirements`, `description`) so all previously enriched records in `jobs.db` remain fully supported.
- **Consequences:** Bulk rescoring (`rescore`) of 1,000+ vacancies completes in memory in `< 0.5s` without any LLM calls, and rule changes can be previewed safely via dry-run (`python -m job_filter rescore --diff`).

---

## ADR-004: Lazy Description Loading Instead of Server-Side Pagination on `GET /api/jobs`

- **Status:** Accepted
- **Context:** As `jobs.db` grew past 800–1,000 vacancies, the `GET /api/jobs` response payload reached ~2.6 MB because it included full Markdown `description` texts for every vacancy. At the same time, the SPA frontend ([`static/js/app.js`](file:///Users/vlad/IdeaProjects/job-filter/static/js/app.js)) builds dynamic filter chips and rejection reason counters (`reasonCounts`, `catCounts`) by iterating over the full array of jobs in the active tab in browser memory.
- **Considered Alternatives:**
  1. *Server-side pagination (`LIMIT / OFFSET`)* — breaks client-side facet counters and requires rewriting search and rejection-reason grouping into complex SQL aggregations.
  2. *Omit `description` from the list query and lazy-load it via `GET /api/jobs/{job_id}/description`* — ~90% of the JSON payload size consisted of the job description text, which is hidden inside a collapsed `<details>` element by default.
- **Decision:** [`jobs_repo.list_all(include_description=False)`](file:///Users/vlad/IdeaProjects/job-filter/job_filter/repositories/jobs_repo.py#L80-L101) returns only lightweight metadata, scores, `enrichment_json`, and a boolean `has_description` flag. The full Markdown description is fetched on demand via [`GET /api/jobs/{job_id}/description`](file:///Users/vlad/IdeaProjects/job-filter/job_filter/api/routers/jobs.py#L53-L61) only when the user expands a vacancy card.
- **Consequences:** The `GET /api/jobs` payload size dropped by more than **10x** (from ~2.6 MB to ~200 KB), initial dashboard rendering is near-instantaneous, and all client-side facet filters remain intact.

---

## ADR-005: Parallel Stateless LLM Workers (`ThreadPoolExecutor`) with Single-Threaded SQLite Persistence

- **Status:** Accepted
- **Context:** The primary bottleneck in the pipeline is the external `agy` CLI subprocess (30–60 seconds per vacancy). However, [`pipeline.py`](file:///Users/vlad/IdeaProjects/job-filter/job_filter/services/pipeline.py) uses a single shared `sqlite3.Connection` per run, and executing concurrent `INSERT/UPDATE` + `commit()` operations across multiple threads causes transaction races and `OperationalError: database is locked`.
- **Considered Alternatives:**
  1. *Sequential loop* — safe for SQLite, but too slow (25–40 minutes for 50 vacancies).
  2. *Full multi-threaded DB access (separate SQLite connection per worker thread)* — introduces SQLite writer contention and complicates log ordering and cancellation.
  3. *Decouple the stateless I/O phase (`ThreadPoolExecutor` for `enrich_job` only) from the persistence phase (main pipeline thread)* — worker threads execute only the pure `enrich_job` subprocess using an immutable snapshot of the candidate context (`load_candidate_context`), while the main thread consumes `as_completed(futures)`, runs deterministic scoring, and writes to SQLite sequentially.
- **Decision:** Implement Alternative 3 in [`pipeline.py`](file:///Users/vlad/IdeaProjects/job-filter/job_filter/services/pipeline.py#L60-L152) with `LLM_ENRICH_WORKERS = 2` and cooperative cancellation via `threading.Event` (`cancel_event`).
- **Consequences:** 2x speedup during the LLM enrichment stage with zero SQLite locking issues and controlled LLM API concurrency.

---

## ADR-006: Custom LinkedIn Guest API Adapter with `Fast-First + Reactive Backoff` Strategy

- **Status:** Accepted
- **Context:** The built-in LinkedIn scraper in `python-jobspy` aborts pagination on the first `HTTP 429` response or transient DNS failure (`NameResolutionError`), losing subsequent pages, and has no awareness of vacancies already stored in `jobs.db`. Conversely, inserting long preventative delays (20–38 seconds) before every request needlessly slows down scraping when LinkedIn's IP token bucket is not exhausted.
- **Considered Alternatives:**
  1. *Retain `python-jobspy` with long fixed delays (20–38s)* — slow and still drops pages whenever a transient `429` occurs.
  2. *Replace LinkedIn search and card hydration with a dedicated adapter ([`job_filter/scraping/linkedin.py`](file:///Users/vlad/IdeaProjects/job-filter/job_filter/scraping/linkedin.py)) using optimistic intervals, session-consistent browser profiles, and early pagination termination via `known_ids_in_run`* — sends requests with short human-like delays (`2.0–3.5s` between pages, `3.5–6.0s` between queries, `1.0–1.8s` per card) using a coherent browser fingerprint (`User-Agent` + `Sec-CH-UA` + XHR/CORS headers), triggering a longer backoff and session reset **only reactively** when an actual `429` or network error occurs.
- **Decision:** Implement Alternative 2 (`scrape_linkedin_search` and `fetch_job_details`). Additionally, pass a cumulative `known_ids_in_run` set across search queries within the same run and stop pagination immediately after encountering a page where all job IDs are already known.
- **Consequences:** LinkedIn scraping runs several times faster without idle 30-second waits, recovers gracefully from `HTTP 429` without losing pages, and avoids wasting IP rate-limit tokens on already-processed listings.
