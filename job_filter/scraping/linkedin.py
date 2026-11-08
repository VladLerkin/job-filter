"""Загрузка поисковой выдачи и детальных карточек вакансий LinkedIn через гостевой API/HTML с защитой от 429 и сбоев DNS."""
from datetime import date
import logging
import random
import re
import time
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from bs4 import BeautifulSoup
from jobspy.linkedin.constant import empty_page, jobs_per_page, max_results
from jobspy.linkedin.util import criteria, is_job_remote, parse_location
from markdownify import markdownify as md
import pandas as pd
import requests

logger = logging.getLogger(__name__)

_BROWSER_PROFILES = (
    {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
    },
    {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
    },
    {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:132.0) Gecko/20100101 Firefox/132.0",
    },
    {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
    },
)


def _build_linkedin_headers(profile: dict[str, str] | None = None, is_xhr: bool = False) -> dict[str, str]:
    chosen = profile or random.choice(_BROWSER_PROFILES)
    headers = {
        "accept": "*/*" if is_xhr else "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9",
        "referer": "https://www.linkedin.com/jobs/search",
        "sec-fetch-dest": "empty" if is_xhr else "document",
        "sec-fetch-mode": "cors" if is_xhr else "navigate",
        "sec-fetch-site": "same-origin",
        **chosen,
    }
    return headers


def scrape_linkedin_search(
    term: str,
    location: str,
    results_wanted: int = 50,
    hours_old: int | None = 24,
    easy_apply: bool | None = None,
    linkedin_company_ids: list[int] | None = None,
    processed_ids: set[str] | None = None,
    page_delay_range: tuple[float, float] = (2.0, 3.5),
    max_retries_per_page: int = 3,
) -> pd.DataFrame:
    """
    Устойчивый скрапер гостевого поиска LinkedIn (/jobs-guest/jobs/api/seeMoreJobPostings/search):
    - Быстрый оптимистичный старт (короткие паузы 2–3.5с между страницами), реактивный backoff только при 429/5xx.
    - Консистентный браузерный профиль (User-Agent + Sec-CH-UA + XHR заголовки) внутри одной сессии;
      полный сброс сессии и смена профиля при 429.
    - Ранний выход при достижении лимита НОВЫХ вакансий или если страница содержит только уже известные БД вакансии.
    """
    session = requests.Session()
    browser_profile = random.choice(_BROWSER_PROFILES)
    params: dict[str, str | int] = {
        "keywords": term,
        "location": location,
        "distance": 50,
    }
    if easy_apply:
        params["f_AL"] = "true"
    if linkedin_company_ids:
        params["f_C"] = ",".join(map(str, linkedin_company_ids))
    if hours_old:
        params["f_TPR"] = f"r{int(hours_old) * 3600}"

    known_ids = processed_ids or set()
    rows: list[dict[str, Any]] = []
    seen_in_run: set[str] = set()
    unseen_collected = 0
    consecutive_all_known_pages = 0
    had_rate_limit = False
    last_error: str | None = None

    start = 0
    while len(rows) < results_wanted and unseen_collected < results_wanted and start < max_results:
        if start > 0:
            time.sleep(random.uniform(*page_delay_range))

        resp = None
        for attempt in range(1, max_retries_per_page + 1):
            try:
                resp = session.get(
                    "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search",
                    params={**params, "start": start},
                    headers=_build_linkedin_headers(browser_profile, is_xhr=True),
                    timeout=15,
                )
                if resp.status_code == 200:
                    last_error = None
                    break
                if resp.status_code == 429:
                    had_rate_limit = True
                    session.close()
                    session = requests.Session()
                    browser_profile = random.choice(_BROWSER_PROFILES)
                    retry_after = resp.headers.get("Retry-After")
                    wait_sec = (
                        float(retry_after)
                        if (retry_after and retry_after.isdigit())
                        else (8.0 * attempt + random.uniform(2.0, 5.0))
                    )
                    logger.warning(
                        "[linkedin] HTTP 429 на '%s' (start=%d, попытка %d/%d), пауза %.1fс...",
                        term, start, attempt, max_retries_per_page, wait_sec,
                    )
                    last_error = f"HTTP 429 Too Many Requests (start={start})"
                    time.sleep(wait_sec)
                    continue
                if resp.status_code in (502, 503, 504):
                    wait_sec = 6.0 * attempt + random.uniform(2.0, 5.0)
                    logger.warning(
                        "[linkedin] HTTP %d на '%s' (start=%d, попытка %d/%d), пауза %.1fс...",
                        resp.status_code, term, start, attempt, max_retries_per_page, wait_sec,
                    )
                    last_error = f"HTTP {resp.status_code} (start={start})"
                    time.sleep(wait_sec)
                    continue
                last_error = f"HTTP {resp.status_code} (start={start})"
                break
            except requests.RequestException as exc:
                wait_sec = 4.0 * attempt + random.uniform(1.5, 3.5)
                logger.warning(
                    "[linkedin] Сбой сети/DNS на '%s' (start=%d, попытка %d/%d): %s. Повтор через %.1fс...",
                    term, start, attempt, max_retries_per_page, exc, wait_sec,
                )
                last_error = f"Network/DNS error: {exc}"
                time.sleep(wait_sec)

        if resp is None or resp.status_code != 200:
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        job_cards = soup.find_all(class_="base-search-card")
        if not job_cards:
            if resp.text.strip() != empty_page and start == 0:
                last_error = "LinkedIn вернул пустую/нестандартную страницу (возможен троттлинг)"
            break

        page_new_cards = 0
        page_unseen_in_db = 0
        for job_card in job_cards:
            raw_urn = str(job_card.get("data-entity-urn", "")).split(":")[-1].strip()
            if not raw_urn or raw_urn in seen_in_run:
                continue
            seen_in_run.add(raw_urn)
            page_new_cards += 1

            full_id = f"li-{raw_urn}"
            if full_id not in known_ids:
                page_unseen_in_db += 1
                unseen_collected += 1

            title_tag = job_card.find("h3", class_="base-search-card__title")
            company_tag = job_card.find("h4", class_="base-search-card__subtitle")
            location_tag = job_card.find("span", class_="job-search-card__location")
            if not title_tag or not company_tag or not location_tag:
                continue

            title = title_tag.get_text(strip=True)
            company = company_tag.get_text(strip=True)
            loc_obj = parse_location(location_tag.get_text(strip=True))
            loc_display = loc_obj.display_location()
            time_tag = job_card.find("time")
            posted_val = None
            if time_tag and time_tag.get("datetime"):
                try:
                    posted_val = date.fromisoformat(str(time_tag["datetime"])).isoformat()
                except ValueError:
                    posted_val = str(time_tag["datetime"])

            rows.append(
                {
                    "id": full_id,
                    "site": "linkedin",
                    "title": title,
                    "company": company,
                    "location": loc_display,
                    "is_remote": is_job_remote(title, loc_obj),
                    "date_posted": posted_val,
                    "job_url": f"https://www.linkedin.com/jobs/view/{raw_urn}",
                }
            )
            if len(rows) >= results_wanted:
                break

        if page_new_cards == 0 or len(job_cards) < jobs_per_page:
            break

        # Если вся страница состоит из уже известных в БД вакансий, не спамим лишними страницами пагинации
        if known_ids and page_unseen_in_db == 0:
            consecutive_all_known_pages += 1
            if consecutive_all_known_pages >= 1:
                logger.info(
                    "[linkedin] Страница (start=%d) содержит только уже известные в БД вакансии — ранняя остановка пагинации.",
                    start,
                )
                break
        else:
            consecutive_all_known_pages = 0

        start += max(len(job_cards), jobs_per_page)

    df = pd.DataFrame(rows)
    df.attrs["had_rate_limit"] = had_rate_limit
    if last_error:
        df.attrs["errors"] = {"linkedin": last_error}
    return df


def extract_linkedin_apply_url(soup: BeautifulSoup) -> str | None:
    """
    Пытается извлечь прямую внешнюю ссылку (applyUrl) из гостевой HTML-карточки LinkedIn,
    если вакансия ведет на внешний ATS (не Easy Apply).
    """
    candidates: list[str] = []

    code_tag = soup.find("code", id="applyUrl")
    if code_tag:
        raw_html = str(code_tag)
        m = re.search(r"<!--\s*\"?(https?://[^\s\"<>]+)\"?\s*-->", raw_html)
        if m:
            candidates.append(m.group(1))
        elif code_tag.get_text(strip=True):
            candidates.append(code_tag.get_text(strip=True).strip('"'))

    for a_tag in soup.find_all("a", href=True):
        cls = " ".join(a_tag.get("class") or [])
        trk = str(a_tag.get("data-tracking-control-name") or "")
        href = str(a_tag["href"])
        if "apply" in cls.lower() or "apply" in trk.lower() or "externalApply" in href:
            candidates.append(href)

    for raw_url in candidates:
        try:
            parsed = urlparse(raw_url)
            qs = parse_qs(parsed.query)
            if "url" in qs and qs["url"]:
                ext = unquote(qs["url"][0]).strip()
                ext_host = (urlparse(ext).hostname or "").lower()
                if ext_host and "linkedin.com" not in ext_host:
                    return ext
            host = (parsed.hostname or "").lower()
            if host and "linkedin.com" not in host:
                return raw_url
        except Exception:
            continue

    return None


def fetch_job_details(
    session: requests.Session,
    job_id: str,
    delay_range: tuple[float, float] = (1.0, 1.8),
    max_retries: int = 3,
    on_retry: Any = None,
) -> dict[str, str | None] | None:
    """
    Догружает полное описание вакансии и метаданные карточки (Seniority, Employment type,
    Job function, Industries, Salary) через гостевой API с короткими паузами и ретраями при 429/502/503.
    """
    raw_id = job_id.removeprefix("li-")
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{raw_id}"
    browser_profile = random.choice(_BROWSER_PROFILES)

    for attempt in range(1, max_retries + 1):
        time.sleep(random.uniform(*delay_range))
        try:
            resp = session.get(url, headers=_build_linkedin_headers(browser_profile, is_xhr=True), timeout=12)
            if resp.status_code == 200:
                if "authwall" in resp.url or "login" in resp.url:
                    session.cookies.clear()
                    browser_profile = random.choice(_BROWSER_PROFILES)
                    logger.warning("[%s] Редирект на authwall (попытка %d/%d)", job_id, attempt, max_retries)
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                div = soup.find("div", class_="show-more-less-html__markup")
                description = md(str(div)).strip() if div else ""

                salary_tag = soup.find("div", class_="compensation__salary")
                salary_text = " ".join(salary_tag.get_text().split()) if salary_tag else None
                apply_url = extract_linkedin_apply_url(soup)

                return {
                    "description": description,
                    "seniority_level": criteria(soup, "Seniority level"),
                    "employment_type": criteria(soup, "Employment type"),
                    "job_function": criteria(soup, "Job function"),
                    "industry": criteria(soup, "Industries"),
                    "salary": salary_text,
                    "apply_url": apply_url,
                }
            elif resp.status_code in (429, 502, 503, 504):
                session.cookies.clear()
                browser_profile = random.choice(_BROWSER_PROFILES)
                backoff = attempt * 4.5 + random.uniform(1.5, 3.5)
                msg = f"  ⏳ [{job_id}] Статус {resp.status_code} (попытка {attempt}/{max_retries}), пауза {backoff:.1f}с..."
                logger.warning(msg)
                if callable(on_retry):
                    on_retry(msg)
                time.sleep(backoff)
            elif resp.status_code == 404:
                return {
                    "description": "",
                    "seniority_level": None,
                    "employment_type": None,
                    "job_function": None,
                    "industry": None,
                    "salary": None,
                    "apply_url": None,
                }
            else:
                logger.warning("[%s] Неожиданный статус %d", job_id, resp.status_code)
        except requests.RequestException as e:
            backoff = attempt * 2.0
            msg = f"  ⏳ [{job_id}] Сбой сети (попытка {attempt}/{max_retries}), повтор через {backoff:.1f}с..."
            logger.warning("[%s] Ошибка сети: %s (попытка %d/%d), ждем %.1fс...", job_id, e, attempt, max_retries, backoff)
            if callable(on_retry):
                on_retry(msg)
            time.sleep(backoff)

    return None

