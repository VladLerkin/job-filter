"""Загрузка детальной карточки вакансии LinkedIn через гостевой API/HTML."""
import logging
import random
import re
import time
from urllib.parse import parse_qs, unquote, urlparse

from bs4 import BeautifulSoup
from jobspy.linkedin.constant import headers as linkedin_headers
from jobspy.linkedin.util import criteria
from markdownify import markdownify as md
import requests

logger = logging.getLogger(__name__)


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
    delay_range: tuple[float, float] = (1.5, 2.5),
    max_retries: int = 3,
) -> dict[str, str | None] | None:
    """
    Догружает полное описание вакансии и метаданные карточки (Seniority, Employment type,
    Job function, Industries, Salary) с паузой и ретраями при 429/502/503.
    """
    raw_id = job_id.removeprefix("li-")
    urls = [
        f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{raw_id}",
        f"https://www.linkedin.com/jobs/view/{raw_id}",
    ]

    for attempt in range(1, max_retries + 1):
        time.sleep(random.uniform(*delay_range))
        url = urls[(attempt - 1) % len(urls)]
        try:
            resp = session.get(url, headers=linkedin_headers, timeout=15)
            if resp.status_code == 200:
                if "authwall" in resp.url or "login" in resp.url:
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
                backoff = attempt * 3.0 + random.uniform(1.0, 2.5)
                logger.warning("[%s] Статус %d (попытка %d/%d), ждем %.1fс...", job_id, resp.status_code, attempt, max_retries, backoff)
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
            logger.warning("[%s] Ошибка сети: %s (попытка %d/%d), ждем %.1fс...", job_id, e, attempt, max_retries, backoff)
            time.sleep(backoff)

    return None

