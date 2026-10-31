"""Адаптер для получения вакансий через Hirify Agent REST API (https://api.hirify.me/api/agent)."""
from datetime import datetime, timezone, timedelta
import logging
import os
import re
from typing import Any
import pandas as pd
import requests

from job_filter import config

logger = logging.getLogger(__name__)


class HirifyClient:
    """REST-клиент для работы с Hirify Agent API."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or config.HIRIFY_API_KEY
        self.base_url = (base_url or config.HIRIFY_API_URL).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "JobFilter/1.0",
            "Accept": "application/json",
        })
        if self.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.api_key}"

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def get_account_status(self) -> dict[str, Any]:
        """GET /api/agent/me: статус аккаунта и остаток дневных квот."""
        resp = self.session.get(f"{self.base_url}/me", timeout=10)
        resp.raise_for_status()
        return resp.json().get("data") or {}

    def search_vacancies(self, filters: dict[str, Any] | None = None, page: int = 1, per_page: int = 50) -> dict[str, Any]:
        """GET /api/agent/vacancies: поиск вакансий (компактные карточки)."""
        params: dict[str, Any] = {
            "page": page,
            "per_page": min(max(per_page, 1), 50),
            "mode": "compact",
        }
        if filters:
            for k, v in filters.items():
                if v is not None:
                    if isinstance(v, (list, dict)):
                        import json
                        params[f"filters[{k}]"] = json.dumps(v)
                    else:
                        params[f"filters[{k}]"] = str(v)

        resp = self.session.get(f"{self.base_url}/vacancies", params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def read_vacancy(self, vacancy_id: int) -> dict[str, Any]:
        """GET /api/agent/vacancies/{vacancy_id}: детальное описание вакансии (тратит суточный лимит opens)."""
        resp = self.session.get(f"{self.base_url}/vacancies/{vacancy_id}", timeout=15)
        resp.raise_for_status()
        return resp.json().get("data") or {}


def _parse_published_date(val: Any) -> datetime | None:
    if not val:
        return None
    val_str = str(val).strip()
    # Поддерживаем форматы ISO8601 (2026-10-30T14:20:00Z, 2026-10-30 14:20:00, 2026-10-30)
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(val_str.replace("Z", "+0000"), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            continue
    return None


def _format_salary(salary_obj: Any) -> str | None:
    if not salary_obj or not isinstance(salary_obj, dict):
        return None
    s_from = salary_obj.get("from")
    s_to = salary_obj.get("to")
    curr = salary_obj.get("currency") or "$"
    period = salary_obj.get("period") or "mo"

    if s_from and s_to:
        return f"{curr}{s_from:,.0f} - {curr}{s_to:,.0f}/{period}"
    elif s_from:
        return f"от {curr}{s_from:,.0f}/{period}"
    elif s_to:
        return f"до {curr}{s_to:,.0f}/{period}"
    return None


def scrape_hirify(
    term: str,
    location: str,
    results_wanted: int = 15,
    hours_old: int = 72,
    client: HirifyClient | None = None,
) -> pd.DataFrame:
    """
    Выполняет поиск вакансий на Hirify по заданным критериям и возвращает DataFrame в стандартном формате JobFilter.
    """
    client = client or HirifyClient()
    df_cols = [
        "id", "site", "job_url", "job_url_direct", "title", "company",
        "location", "date_posted", "salary", "description", "is_remote",
        "job_level", "job_type",
    ]

    if not client.is_configured():
        msg = "HIRIFY_API_KEY не установлен. Укажите ключ в переменной окружения HIRIFY_API_KEY."
        logger.warning(msg)
        df_empty = pd.DataFrame(columns=df_cols)
        df_empty.attrs["errors"] = {"hirify": msg}
        return df_empty

    clean_term = re.sub(r"\bremote\b", "", term, flags=re.IGNORECASE).strip() or term

    # Формируем фильтры Hirify
    filters: dict[str, Any] = {
        "search": clean_term,
        "work_format": ["remote"],
        "worldwide_remote": True,
        "sort_by": "date",
    }

    loc_lower = (location or "").lower()
    if "georgia" in loc_lower or "ge" == loc_lower:
        filters["my_location"] = "GE"
    elif "uk" in loc_lower or "united kingdom" in loc_lower:
        filters["my_location"] = "GB"
    elif "poland" in loc_lower:
        filters["my_location"] = "PL"
    elif "germany" in loc_lower:
        filters["my_location"] = "DE"

    try:
        search_res = client.search_vacancies(filters=filters, page=1, per_page=min(results_wanted * 2, 50))
    except Exception as e:
        err_msg = f"Ошибка запроса к Hirify API: {e}"
        logger.error(err_msg)
        df_empty = pd.DataFrame(columns=df_cols)
        df_empty.attrs["errors"] = {"hirify": err_msg}
        return df_empty

    cards = search_res.get("data") or []
    if not isinstance(cards, list):
        cards = []

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=hours_old) if hours_old and hours_old > 0 else None

    matched_rows = []
    for card in cards:
        if len(matched_rows) >= results_wanted:
            break

        vac_id = card.get("vacancy_id")
        if not vac_id:
            continue

        pub_dt = _parse_published_date(card.get("published_at") or card.get("created_at"))
        if cutoff and pub_dt and pub_dt < cutoff:
            # Старше заданного интервала времени
            continue

        slug = card.get("slug") or str(vac_id)
        job_url = f"https://hirify.me/vacancies/{slug}"
        title = card.get("title") or "Unknown Title"
        company = card.get("company") or ("Confidential" if card.get("company_masked") else "Hirify Employer")

        # Локация / Регионы
        regions = card.get("regions") or []
        remote_type = card.get("remote_type") or "Remote"
        loc_display = f"{remote_type} ({', '.join(regions)})" if regions else remote_type

        # Уровень должности
        grades = card.get("grades") or []
        job_level = ", ".join(grades) if grades else "Senior"

        # Загружаем полное описание вакансии (vacancies.read)
        desc_text = ""
        try:
            detail = client.read_vacancy(vac_id)
            desc_text = detail.get("description") or detail.get("original_description") or ""
            if not company or company == "Hirify Employer":
                company = detail.get("company") or company
        except Exception as e:
            logger.warning(f"Не удалось загрузить детальное описание Hirify вакансии #{vac_id}: {e}")
            desc_text = f"{title}\nSkills: {', '.join(card.get('skills') or [])}"

        matched_rows.append({
            "id": f"hf-{vac_id}",
            "site": "hirify",
            "job_url": job_url,
            "job_url_direct": None,
            "title": title,
            "company": company,
            "location": loc_display,
            "date_posted": pub_dt.strftime("%Y-%m-%d") if pub_dt else now.strftime("%Y-%m-%d"),
            "salary": _format_salary(card.get("salary")),
            "description": desc_text,
            "is_remote": True,
            "job_level": job_level,
            "job_type": "full_time",
        })

    return pd.DataFrame(matched_rows, columns=df_cols)
