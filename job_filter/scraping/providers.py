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
) -> pd.DataFrame:
    """Вызывает JobSpy или специализированный адаптер для проверенных провайдеров (LinkedIn, Indeed, Glassdoor, Hirify)."""
    site = (site or "linkedin").strip().lower()
    if site not in SUPPORTED_SITES:
        raise ValueError(f"Неподдерживаемый или заблокированный провайдер '{site}'. Доступны только: {', '.join(SUPPORTED_SITES)}")

    clean_term = re.sub(r"\bremote\b", "", term, flags=re.IGNORECASE).strip() or term

    if site == "hirify":
        from job_filter.scraping.hirify_adapter import scrape_hirify
        return scrape_hirify(
            term=term,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
        )

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

    raise ValueError(f"Неизвестный провайдер: {site}")

