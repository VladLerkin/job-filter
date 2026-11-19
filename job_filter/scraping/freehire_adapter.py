"""Адаптер для получения вакансий через FreeHire Public/Agent API (https://freehire.me/api/v1)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
import math
import re
import time
from typing import Any

import pandas as pd
import requests

from job_filter import config

logger = logging.getLogger(__name__)

DF_COLS = [
    "id", "site", "job_url", "job_url_direct", "title", "company",
    "location", "date_posted", "salary", "description", "is_remote",
    "job_level", "job_type",
]

# Фасеты, которые мы передаём в FreeHire API как списки (через запятую)
ARRAY_FACET_KEYS = (
    "ai_archetype",
    "ai_archetype_exclude",
    "category",
    "category_exclude",
    "seniority",
    "seniority_exclude",
    "work_mode",
    "work_mode_exclude",
    "work_mode_remote_regions",
    "work_mode_remote_countries",
    "regions",
    "regions_exclude",
    "countries",
    "countries_exclude",
    "skills",
    "skills_exclude",
    "domains",
    "domains_exclude",
    "employment_type",
    "employment_type_exclude",
    "posting_language",
    "posting_language_exclude",
    "reality",
    "reality_exclude",
    "equity",
    "equity_exclude",
    "is_tech",
    "source",
    "source_exclude",
    "source_type",
    "source_type_exclude",
    "company_type",
    "company_type_exclude",
    "company_size",
    "collections",
)

# Булевы фасеты FreeHire API
BOOL_FACET_KEYS = (
    "work_mode_remote_anywhere",
    "via_recruiter",
    "requires_clearance",
    "visa_sponsorship",
    "auto_apply_available",
    "seniority_include_unspecified",
)

# Строковые/числовые фасеты
SCALAR_FACET_KEYS = (
    "q",
    "skills_mode",
    "category_mode",
    "salary_min",
    "salary_max",
    "experience_years_min",
    "experience_years_max",
    "posted_within_days",
)

# Дефолтный набор фасетов (оптимизирован для поиска Senior/Lead Remote Tech/AI ролей)
DEFAULT_FREEHIRE_FACETS: dict[str, Any] = {
    "q": "",
    "ai_archetype": [],
    "category": ["ai_engineering", "backend", "software_engineering", "ml_ai"],
    "seniority": ["senior", "lead", "staff", "principal"],
    "seniority_exclude": ["intern", "junior"],
    "work_mode": ["remote"],
    "work_mode_remote_anywhere": False,
    "work_mode_remote_regions": [],
    "regions": [],
    "skills": [],
    "skills_mode": "or",
    "reality": ["fresh"],
    "posting_language": ["en"],
    "is_tech": ["tech"],
    "equity_exclude": ["equity_only"],
    "via_recruiter": False,
    "requires_clearance": False,
    "source_type": [],
    "source_exclude": [],
    "exclude_blacklisted_ats": True,
}

# Маппинг доменов ATS из чёрного списка job-filter на слаги `source` в FreeHire
ATS_DOMAIN_TO_FREEHIRE_SOURCE: dict[str, str] = {
    "myworkdayjobs.com": "workday",
    "workday.com": "workday",
    "taleo.net": "taleo",
    "icims.com": "icims",
    "smartrecruiters.com": "smartrecruiters",
    "successfactors.com": "successfactors",
    "successfactors.eu": "successfactors",
    "oraclecloud.com": "oracle",
    "greenhouse.io": "greenhouse",
    "lever.co": "lever",
    "ashbyhq.com": "ashby",
    "bamboohr.com": "bamboohr",
    "breezy.hr": "breezy",
    "workable.com": "workable",
    "recruitee.com": "recruitee",
    "jobvite.com": "jobvite",
    "ultipro.com": "ukg",
    "ukg.com": "ukg",
    "paylocity.com": "paylocity",
    "adp.com": "adp",
    "avature.net": "avature",
    "brassring.com": "brassring",
    "dayforcehcm.com": "dayforce",
    "rippling.com": "rippling",
    "personio.de": "personio",
    "personio.com": "personio",
    "teamtailor.com": "teamtailor",
    "jazzhr.com": "jazzhr",
}

_BASE_FACETS_CACHE: dict[str, Any] = {"ts": 0.0, "data": None}
_BASE_FACETS_TTL_SEC = 600  # 10 минут


def map_blacklisted_domains_to_freehire_sources(domains: list[str] | None) -> list[str]:
    """Преобразует домены из чёрного списка job-filter в известные слаги `source` FreeHire."""
    if not domains:
        return []
    sources: set[str] = set()
    for raw in domains:
        d = (raw or "").strip().lower()
        if not d:
            continue
        if d in ATS_DOMAIN_TO_FREEHIRE_SOURCE:
            sources.add(ATS_DOMAIN_TO_FREEHIRE_SOURCE[d])
            continue
        for known_domain, fh_src in ATS_DOMAIN_TO_FREEHIRE_SOURCE.items():
            if d.endswith("." + known_domain) or known_domain in d:
                sources.add(fh_src)
                break
    return sorted(sources)


def _slugify_skill(name: str) -> str:
    s = (name or "").strip().lower()
    s = s.replace("c++", "cpp").replace("c#", "csharp").replace(".net", "dotnet")
    s = re.sub(r"[/\s_]+", "-", s)
    s = re.sub(r"[^a-z0-9.+-]", "", s)
    return s.strip("-")


def match_profile_skills_to_freehire(
    candidate_aliases: set[str],
    available_skills: dict[str, int],
    max_skills: int = 20,
) -> list[dict[str, Any]]:
    """Сопоставляет навыки кандидата из Skills Matrix с каноническими слагами фасета `skills` FreeHire."""
    if not candidate_aliases or not available_skills:
        return []

    avail_lower = {k.lower(): (k, int(v)) for k, v in available_skills.items()}
    matched: dict[str, int] = {}

    for alias in candidate_aliases:
        raw = (alias or "").strip().lower()
        if not raw:
            continue
        candidates = {raw, _slugify_skill(raw), raw.replace(" ", "-"), raw.replace("-", "")}
        for cand in candidates:
            if cand and cand in avail_lower:
                canon, cnt = avail_lower[cand]
                matched[canon] = cnt
                break

    ranked = sorted(matched.items(), key=lambda item: (-item[1], item[0]))
    return [{"slug": slug, "count": cnt} for slug, cnt in ranked[:max_skills]]


def build_freehire_query_params(
    facets_cfg: dict[str, Any] | None,
    *,
    extra_source_exclude: list[str] | None = None,
) -> dict[str, Any]:
    """Формирует словарь query-параметров для FreeHire API из конфигурации фасетов."""
    cfg = dict(facets_cfg or {})
    params: dict[str, Any] = {}

    for key in ARRAY_FACET_KEYS:
        val = cfg.get(key)
        if isinstance(val, str):
            items = [x.strip() for x in val.split(",") if x.strip()]
        elif isinstance(val, (list, tuple, set)):
            items = [str(x).strip() for x in val if str(x).strip()]
        else:
            items = []

        if key == "source_exclude" and extra_source_exclude:
            items = sorted(set(items) | {s.strip() for s in extra_source_exclude if s and s.strip()})

        if items:
            params[key] = ",".join(items)

    # Если source_exclude не было в cfg, но пришло из extra_source_exclude
    if "source_exclude" not in params and extra_source_exclude:
        cleaned = sorted({s.strip() for s in extra_source_exclude if s and s.strip()})
        if cleaned:
            params["source_exclude"] = ",".join(cleaned)

    for key in BOOL_FACET_KEYS:
        val = cfg.get(key)
        if val is None or val == "":
            continue
        # work_mode_remote_anywhere имеет смысл передавать только когда True
        if key in ("work_mode_remote_anywhere", "visa_sponsorship", "auto_apply_available", "seniority_include_unspecified"):
            if bool(val) is True:
                params[key] = "true"
        else:
            # via_recruiter / requires_clearance: False означает явное исключение (передаём "false")
            if isinstance(val, bool):
                params[key] = "true" if val else "false"
            elif isinstance(val, str) and val.lower() in ("true", "false"):
                params[key] = val.lower()

    for key in SCALAR_FACET_KEYS:
        val = cfg.get(key)
        if val is None:
            continue
        if key == "skills_mode":
            # FreeHire поддерживает только skills_mode=and (по умолчанию OR)
            if str(val).strip().lower() == "and" and params.get("skills"):
                params["skills_mode"] = "and"
            continue
        if key == "category_mode":
            if str(val).strip().lower() == "and" and params.get("category"):
                params["category_mode"] = "and"
            continue
        s_val = str(val).strip()
        if s_val:
            params[key] = s_val

    return params


def _parse_iso_datetime(val: Any) -> datetime | None:
    if not val:
        return None
    s = str(val).strip()
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _format_salary(job: dict[str, Any]) -> str | None:
    s_min = job.get("salary_min")
    s_max = job.get("salary_max")
    if s_min is None and s_max is None:
        enr = job.get("enrichment") or {}
        s_min = enr.get("salary_min")
        s_max = enr.get("salary_max")
        curr = enr.get("salary_currency") or job.get("salary_currency") or "USD"
        period = enr.get("salary_period") or job.get("salary_period") or "year"
    else:
        curr = job.get("salary_currency") or "USD"
        period = job.get("salary_period") or "year"

    if s_min is not None and s_max is not None:
        return f"{curr} {s_min:,.0f} - {s_max:,.0f}/{period}"
    if s_min is not None:
        return f"from {curr} {s_min:,.0f}/{period}"
    if s_max is not None:
        return f"up to {curr} {s_max:,.0f}/{period}"
    return None


def _format_location(job: dict[str, Any]) -> str:
    work_mode = (job.get("work_mode") or "").strip().lower()
    raw_loc = (job.get("location") or "").strip()
    regions = [str(r).upper() for r in (job.get("regions") or []) if r]
    countries = [str(c).upper() for c in (job.get("countries") or []) if c]

    geo_parts = []
    if raw_loc:
        geo_parts.append(raw_loc)
    elif countries:
        geo_parts.append(", ".join(countries[:4]))
    elif regions:
        geo_parts.append(", ".join(regions[:3]))

    prefix = "Remote" if work_mode == "remote" else ("Hybrid" if work_mode == "hybrid" else "")
    if prefix and geo_parts:
        if prefix.lower() in geo_parts[0].lower():
            return geo_parts[0]
        return f"{prefix} ({geo_parts[0]})"
    if prefix:
        return prefix
    return geo_parts[0] if geo_parts else "Worldwide"


class FreeHireClient:
    """HTTP-клиент для публичного и агентского API FreeHire."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key if api_key is not None else config.FREEHIRE_API_KEY
        self.base_url = (base_url or config.FREEHIRE_API_URL).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"job-filter/{config.APP_VERSION} (+https://github.com/vlad/job-filter)",
            "Accept": "application/json",
        })
        if self.api_key and self.api_key.strip():
            self.session.headers["Authorization"] = f"Bearer {self.api_key.strip()}"

    def _check_rate_limit(self, resp: requests.Response) -> None:
        rem = resp.headers.get("X-RateLimit-Remaining")
        if rem is not None:
            try:
                if int(rem) <= 2:
                    reset_sec = min(int(resp.headers.get("X-RateLimit-Reset") or 2), 5)
                    logger.info("FreeHire rate limit близок к исчерпанию, пауза %sс", reset_sec)
                    time.sleep(max(1, reset_sec))
            except ValueError:
                pass

    def _warn_ignored_params(self, payload: dict[str, Any]) -> None:
        meta = payload.get("meta") or {}
        ignored = meta.get("ignored_params")
        if ignored:
            logger.warning("FreeHire API проигнорировал параметры: %s", ignored)

    def get_facets(
        self,
        facets_cfg: dict[str, Any] | None = None,
        *,
        facet_keys: list[str] | None = None,
        extra_source_exclude: list[str] | None = None,
        use_base_cache: bool = False,
    ) -> dict[str, Any]:
        """GET /jobs/facets — возвращает живой словарь фасетов и количество вакансий по срезу."""
        params = build_freehire_query_params(facets_cfg, extra_source_exclude=extra_source_exclude)
        if facet_keys:
            params["facets"] = ",".join(facet_keys)

        is_base_call = use_base_cache and not params
        if is_base_call:
            now = time.monotonic()
            if _BASE_FACETS_CACHE["data"] is not None and (now - _BASE_FACETS_CACHE["ts"]) < _BASE_FACETS_TTL_SEC:
                return _BASE_FACETS_CACHE["data"]

        resp = self.session.get(f"{self.base_url}/jobs/facets", params=params, timeout=20)
        resp.raise_for_status()
        self._check_rate_limit(resp)
        payload = resp.json()
        self._warn_ignored_params(payload)
        data = payload.get("data") or {}

        if is_base_call:
            _BASE_FACETS_CACHE["ts"] = time.monotonic()
            _BASE_FACETS_CACHE["data"] = data

        return data

    def search_jobs(
        self,
        facets_cfg: dict[str, Any] | None = None,
        *,
        limit: int = 50,
        offset: int = 0,
        description_format: str = "markdown",
        sort: str = "posted_at",
        order: str = "desc",
        extra_source_exclude: list[str] | None = None,
    ) -> dict[str, Any]:
        """GET /agent/jobs/search — поиск с полными описаниями в одном запросе."""
        params = build_freehire_query_params(facets_cfg, extra_source_exclude=extra_source_exclude)
        params["limit"] = min(max(int(limit), 1), 50)
        params["offset"] = max(int(offset), 0)
        params["description_format"] = description_format
        params["sort"] = sort
        params["order"] = order

        resp = self.session.get(f"{self.base_url}/agent/jobs/search", params=params, timeout=25)
        resp.raise_for_status()
        self._check_rate_limit(resp)
        payload = resp.json()
        self._warn_ignored_params(payload)
        return payload


def scrape_freehire(
    facets: dict[str, Any] | None = None,
    results_wanted: int = 50,
    hours_old: int = 24,
    term: str = "",
    processed_ids: set[str] | None = None,
    blacklisted_domains: list[str] | None = None,
    client: FreeHireClient | None = None,
) -> pd.DataFrame:
    """Собирает вакансии из FreeHire по заданным фасетам и возвращает DataFrame формата DF_COLS."""
    fh = client or FreeHireClient()
    eff_facets = dict(DEFAULT_FREEHIRE_FACETS)
    if facets:
        eff_facets.update(facets)

    # Опциональный текстовый запрос q (Вариант A: если явно указан в facets['q'] или передан term)
    if not (eff_facets.get("q") or "").strip() and (term or "").strip():
        eff_facets["q"] = term.strip()

    # Вычисляем posted_within_days на основе hours_old, если пользователь не задал вручную
    if hours_old and hours_old > 0 and not eff_facets.get("posted_within_days"):
        eff_facets["posted_within_days"] = max(1, math.ceil(hours_old / 24.0))

    extra_source_exclude: list[str] = []
    if eff_facets.get("exclude_blacklisted_ats", True) and blacklisted_domains:
        extra_source_exclude = map_blacklisted_domains_to_freehire_sources(blacklisted_domains)

    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(hours=hours_old) if hours_old and hours_old > 0 else None

    rows: list[dict[str, Any]] = []
    seen_slugs: set[str] = set()
    errors: dict[str, str] = {}
    total_available = 0

    page_size = min(50, max(10, results_wanted))
    max_pages = max(2, min(6, math.ceil(results_wanted / page_size) + 2))
    offset = 0

    for _ in range(max_pages):
        if len(rows) >= results_wanted:
            break
        try:
            payload = fh.search_jobs(
                eff_facets,
                limit=page_size,
                offset=offset,
                description_format="markdown",
                sort="posted_at",
                order="desc",
                extra_source_exclude=extra_source_exclude,
            )
        except Exception as exc:
            logger.error("Ошибка запроса к FreeHire API: %s", exc)
            errors["freehire"] = str(exc)
            break

        meta = payload.get("meta") or {}
        total_available = int(meta.get("total") or 0)
        items = payload.get("data") or []
        if not items:
            break

        stop_due_to_age = False
        for item in items:
            if len(rows) >= results_wanted:
                break
            slug = (item.get("public_slug") or "").strip()
            if not slug or slug in seen_slugs:
                continue
            seen_slugs.add(slug)

            job_key = f"fh-{slug}"
            if processed_ids and job_key in processed_ids:
                continue

            posted_raw = item.get("posted_at") or item.get("created_at")
            posted_dt = _parse_iso_datetime(posted_raw)
            if cutoff and posted_dt and posted_dt < cutoff:
                # Т.к. выдача отсортирована по posted_at desc, дальше будут ещё более старые
                stop_due_to_age = True
                continue

            enr = item.get("enrichment") or {}
            work_mode = (item.get("work_mode") or "").strip().lower()
            is_remote = work_mode == "remote"

            direct_url = (item.get("url") or "").strip() or None
            freehire_url = f"https://freehire.me/jobs/{slug}"

            rows.append({
                "id": job_key,
                "site": "freehire",
                "job_url": freehire_url,
                "job_url_direct": direct_url,
                "title": (item.get("title") or "Unknown Title").strip(),
                "company": (item.get("company") or "Unknown Company").strip(),
                "location": _format_location(item),
                "date_posted": posted_dt.strftime("%Y-%m-%d") if posted_dt else str(posted_raw or ""),
                "salary": _format_salary(item),
                "description": (item.get("description") or "").strip(),
                "is_remote": is_remote,
                "job_level": enr.get("seniority") or None,
                "job_type": enr.get("employment_type") or None,
            })

        if stop_due_to_age or len(items) < page_size:
            break
        offset += len(items)

    df = pd.DataFrame(rows, columns=DF_COLS) if rows else pd.DataFrame(columns=DF_COLS)
    df.attrs["total_available"] = total_available
    if errors:
        df.attrs["errors"] = errors
    return df
