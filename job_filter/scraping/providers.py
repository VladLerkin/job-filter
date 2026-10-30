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


def scrape_site(
    site: str,
    term: str,
    location: str,
    country_indeed: str,
    results_wanted: int,
    hours_old: int,
    easy_apply: bool | None,
    linkedin_company_ids: list[int] | None = None,
) -> pd.DataFrame:
    """Вызывает JobSpy scrape_jobs с оптимизированными под каждый сайт параметрами."""
    clean_term = re.sub(r"\bremote\b", "", term, flags=re.IGNORECASE).strip() or term

    if site == "linkedin":
        return scrape_jobs(
            site_name=["linkedin"],
            search_term=term,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            easy_apply=easy_apply,
            linkedin_company_ids=linkedin_company_ids,
            fetch_description=False,
        )

    if site == "indeed":
        target_country = (location or country_indeed or "uk").strip().lower()
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
        target_country = (location or country_indeed or "uk").strip().lower()
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

    if site == "google":
        time_str = "since yesterday" if hours_old <= 24 else "in the last 3 days" if hours_old <= 72 else "in the last week"
        g_query = f"{clean_term} remote jobs in {location} {time_str}"
        return scrape_jobs(
            site_name=["google"],
            search_term=clean_term,
            google_search_term=g_query,
            location=location,
            is_remote=True,
            results_wanted=results_wanted,
            hours_old=hours_old,
            fetch_description=True,
        )

    if site == "zip_recruiter":
        zr_loc = None if location.lower() in ("remote", "usa", "united states") else location
        return scrape_jobs(
            site_name=["zip_recruiter"],
            search_term=clean_term,
            location=zr_loc,
            is_remote=True,
            results_wanted=results_wanted,
            hours_old=hours_old,
            easy_apply=easy_apply,
            fetch_description=True,
        )

    if site == "hellowork":
        hw_loc = None if location.lower() in ("france", "remote", "télétravail") else location
        return scrape_jobs(
            site_name=["hellowork"],
            search_term=clean_term,
            location=hw_loc,
            is_remote=True,
            results_wanted=results_wanted,
            hours_old=hours_old,
            fetch_description=True,
        )

    if site == "bayt":
        bayt_loc = None if location.lower() in ("all", "mena", "remote") else location
        return scrape_jobs(
            site_name=["bayt"],
            search_term=clean_term,
            location=bayt_loc,
            is_remote=True,
            results_wanted=results_wanted,
            hours_old=hours_old,
            easy_apply=easy_apply,
            fetch_description=True,
        )

    # Общий случай для остальных провайдеров
    return scrape_jobs(
        site_name=[site],
        search_term=clean_term,
        location=location,
        country_indeed=country_indeed,
        is_remote=True,
        results_wanted=results_wanted,
        hours_old=hours_old,
        easy_apply=easy_apply,
        fetch_description=True,
    )

