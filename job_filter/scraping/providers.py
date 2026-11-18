"""Адаптеры поиска вакансий для проверенных площадок (LinkedIn, Hirify, Upwork)."""
import logging
import re
import pandas as pd

logger = logging.getLogger(__name__)

SUPPORTED_SITES = ("linkedin", "hirify", "upwork")


def scrape_site(
    site: str,
    term: str,
    location: str,
    results_wanted: int,
    hours_old: int,
    easy_apply: bool | None,
    country_indeed: str = "uk",
    linkedin_company_ids: list[int] | None = None,
    hirify_mode: str = "feeds",
    hirify_feed_id: int | str | None = None,
    processed_ids: set[str] | None = None,
) -> pd.DataFrame:
    """Вызывает специализированный адаптер для проверенных провайдеров (LinkedIn, Hirify, Upwork)."""
    site = (site or "linkedin").strip().lower()
    if site not in SUPPORTED_SITES:
        raise ValueError(f"Неподдерживаемый или заблокированный провайдер '{site}'. Доступны только: {', '.join(SUPPORTED_SITES)}")

    clean_term = re.sub(r"\bremote\b", "", term, flags=re.IGNORECASE).strip() or term

    if site == "upwork":
        from job_filter.scraping.upwork_adapter import scrape_upwork

        return scrape_upwork(
            term=term,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            processed_ids=processed_ids,
        )

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

    raise ValueError(f"Неизвестный провайдер: {site}")
