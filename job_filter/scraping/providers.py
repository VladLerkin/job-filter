"""Адаптеры вызова JobSpy для поддерживаемых сайтов поиска вакансий."""
import logging
import re
from typing import Any
import pandas as pd
from jobspy import scrape_jobs

logger = logging.getLogger(__name__)

GLASSDOOR_COUNTRY_NAMES = {
    "uk": "United Kingdom",
    "germany": "Germany",
    "netherlands": "Netherlands",
    "france": "France",
    "spain": "Spain",
    "ireland": "Ireland",
    "switzerland": "Switzerland",
    "austria": "Austria",
    "belgium": "Belgium",
    "italy": "Italy",
    "usa": "United States",
    "canada": "Canada",
}

INDEED_COUNTRY_ALIASES = {
    "czechrepublic": "czech republic",
    "czechia": "czech republic",
    "unitedarabemirates": "united arab emirates",
    "uae": "united arab emirates",
    "united kingdom": "uk",
    "great britain": "uk",
    "gb": "uk",
    "united states": "usa",
    "us": "usa",
    "remote": "uk",
    "emea": "uk",
    "worldwide": "uk",
}


def normalize_indeed_country(country_indeed: str | None, location: str | None) -> str:
    raw = (country_indeed or "").strip().lower()
    if not raw or raw == "remote" or (raw == "uk" and location and location.strip().lower() not in ("", "remote", "emea", "worldwide")):
        loc_cand = (location or "").strip().lower()
        if loc_cand and loc_cand not in ("remote", "emea", "worldwide"):
            raw = loc_cand
    raw = raw or "uk"
    return INDEED_COUNTRY_ALIASES.get(raw, raw)


SUPPORTED_SITES = ("linkedin", "indeed", "glassdoor", "hirify")


def scrape_site(
    site: str,
    term: str,
    location: str,
    country_indeed: str,
    results_wanted: int,
    hours_old: int,
    easy_apply: bool | None,
    linkedin_company_ids: list[int] | None = None,
    hirify_mode: str = "feeds",
    hirify_feed_id: int | str | None = None,
    processed_ids: set[str] | None = None,
) -> pd.DataFrame:
    """Вызывает JobSpy или специализированный адаптер для проверенных провайдеров (LinkedIn, Indeed, Glassdoor, Hirify)."""
    site = (site or "linkedin").strip().lower()
    if site not in SUPPORTED_SITES:
        raise ValueError(f"Неподдерживаемый или заблокированный провайдер '{site}'. Доступны только: {', '.join(SUPPORTED_SITES)}")

    clean_term = re.sub(r"\bremote\b", "", term, flags=re.IGNORECASE).strip() or term

    if site == "hirify":
        from job_filter.scraping.hirify_adapter import (
            scrape_hirify,
            scrape_hirify_feed,
            scrape_hirify_active_feeds,
        )
        if hirify_mode == "feeds":
            if hirify_feed_id is not None and str(hirify_feed_id).strip() not in ("", "all_active", "all"):
                try:
                    feed_id_int = int(hirify_feed_id)
                    return scrape_hirify_feed(
                        feed_id=feed_id_int,
                        results_wanted=results_wanted,
                        hours_old=hours_old,
                        processed_ids=processed_ids,
                    )
                except ValueError:
                    logger.warning("Некорректный feed_id %s, переключаемся на все активные фильтры", hirify_feed_id)
            return scrape_hirify_active_feeds(
                results_wanted=results_wanted,
                hours_old=hours_old,
                processed_ids=processed_ids,
            )

        return scrape_hirify(
            term=term,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            processed_ids=processed_ids,
        )

    if site == "linkedin":
        from job_filter.scraping.linkedin import scrape_linkedin_search

        return scrape_linkedin_search(
            term=term,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            easy_apply=easy_apply,
            linkedin_company_ids=linkedin_company_ids,
            processed_ids=processed_ids,
        )

    if site == "indeed":
        target_country = normalize_indeed_country(country_indeed, location)
        return scrape_jobs(
            site_name=["indeed"],
            search_term=clean_term,
            location=None,
            country_indeed=target_country,
            is_remote=True,
            results_wanted=results_wanted,
            hours_old=hours_old,
            easy_apply=easy_apply,
            fetch_description=True,
        )

    if site == "glassdoor":
        target_country = normalize_indeed_country(country_indeed, location)
        gd_loc = GLASSDOOR_COUNTRY_NAMES.get(target_country, location)
        return scrape_jobs(
            site_name=["glassdoor"],
            search_term=clean_term,
            location=gd_loc,
            country_indeed=target_country,
            is_remote=True,
            results_wanted=results_wanted,
            hours_old=hours_old,
            easy_apply=easy_apply,
            fetch_description=True,
        )

    raise ValueError(f"Неизвестный провайдер: {site}")

