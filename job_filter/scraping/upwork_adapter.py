"""Адаптер для получения фриланс-контрактов и вакансий Upwork через Apify Actors REST API."""
from datetime import datetime, timedelta, timezone
import logging
import re
from typing import Any
import pandas as pd
import requests

from job_filter import config

logger = logging.getLogger(__name__)

# Упорядоченный список проверенных Pay-Per-Event / Free-Tier акторов Upwork на Apify
FALLBACK_UPWORK_ACTORS: tuple[str, ...] = (
    "blackfalcondata~upwork-scraper",
    "hyperbach~upwork-scraper-ai",
    "flash_mage~upwork",
    "deltaspider~upwork-job-scraper",
    "devcake~upwork-jobs-scraper",
)

DF_COLS = [
    "id",
    "site",
    "job_url",
    "job_url_direct",
    "title",
    "company",
    "location",
    "date_posted",
    "salary",
    "description",
    "is_remote",
    "job_level",
    "job_type",
]

EUROPE_COUNTRIES = frozenset({
    "united kingdom", "uk", "great britain", "england", "scotland", "wales", "ireland",
    "germany", "france", "netherlands", "belgium", "luxembourg", "switzerland", "austria",
    "spain", "portugal", "italy", "greece", "cyprus", "malta", "poland", "czechia",
    "czech republic", "slovakia", "hungary", "romania", "bulgaria", "croatia", "slovenia",
    "serbia", "montenegro", "estonia", "latvia", "lithuania", "sweden", "norway",
    "finland", "denmark", "iceland", "ukraine", "georgia", "armenia",
})

EMEA_COUNTRIES = EUROPE_COUNTRIES | frozenset({
    "united arab emirates", "uae", "israel", "saudi arabia", "qatar", "bahrain",
    "kuwait", "oman", "turkey", "türkiye", "egypt", "south africa", "morocco",
    "tunisia", "kenya", "nigeria",
})


def normalize_actor_id(actor_id: str) -> str:
    """Преобразует 'user/actor-name' в формат Apify API 'user~actor-name'."""
    cleaned = (actor_id or "").strip().strip("/")
    return cleaned.replace("/", "~") if cleaned else "blackfalcondata~upwork-scraper"


def _build_actor_input(
    actor_id: str,
    query: str,
    results_wanted: int = 50,
    hours_old: int = 24,
    payment_verified_only: bool = False,
) -> dict[str, Any]:
    """Формирует входной JSON-пейлоад под схему конкретного Apify-актора Upwork."""
    norm_id = normalize_actor_id(actor_id).lower()
    clean_q = (query or "").strip()
    limit_val = max(1, min(int(results_wanted or 50), 250))
    hours_val = max(1, int(hours_old or 24))

    if "blackfalcondata~" in norm_id:
        return {
            "query": clean_q,
            "sort": "recency",
            "maxResults": limit_val,
            "maxAgeMinutes": hours_val * 60,
            "verifiedPaymentOnly": bool(payment_verified_only),
        }

    if "hyperbach~" in norm_id:
        return {
            "keywords": [clean_q] if clean_q else [],
            "limit": limit_val,
        }

    if "flash_mage~" in norm_id:
        return {
            "query": [clean_q] if clean_q else [],
            "limit": limit_val,
            "sort": "newest",
        }

    if "deltaspider~" in norm_id:
        return {
            "userQuery": clean_q,
            "limit": limit_val,
            "maxJobAgeHours": hours_val,
            "sort": "recency",
        }

    if "devcake~" in norm_id:
        return {
            "searchQueries": [clean_q] if clean_q else [],
            "maxItems": limit_val,
            "sort": "newest",
        }

    if "neatrat~" in norm_id:
        payload: dict[str, Any] = {
            "query": clean_q,
            "experienceLevel": ["intermediate", "expert"],
            "jobType": ["fixed", "hourly"],
            "clientPaymentVerifiedOnly": bool(payment_verified_only),
            "maxJobAge": {
                "value": hours_val,
                "unit": "hours",
            },
        }
        return payload

    if "fasty_dev~" in norm_id:
        return {
            "keywords": clean_q,
            "limit": max(10, limit_val),
            "offset": 0,
            "sortby": "newest",
            "client_payment_verified": bool(payment_verified_only),
        }

    if "omkarcloud~" in norm_id:
        pages = max(1, min(5, (limit_val + 9) // 10))
        return {
            "query": clean_q,
            "page": 1,
            "pageStart": 1,
            "pageEnd": pages,
        }

    if "accountable_eel~" in norm_id:
        return {
            "queries": [clean_q] if clean_q else ["software engineer"],
            "includeKeywords": [],
            "excludeKeywords": [],
        }

    if "upwork-vibe~" in norm_id:
        from_dt = (datetime.now(timezone.utc) - timedelta(hours=hours_val)).strftime("%Y-%m-%d")
        return {
            "searchQuery": clean_q,
            "query": clean_q,
            "limit": limit_val,
            "maxItems": limit_val,
            "fromDate": from_dt,
        }

    # Универсальный фоллбэк-пейлоад для пользовательских акторов Upwork
    return {
        "query": clean_q,
        "queries": [clean_q] if clean_q else [],
        "keywords": clean_q,
        "searchQuery": clean_q,
        "maxItems": limit_val,
        "limit": max(10, limit_val),
        "item_limit": limit_val,
        "experienceLevel": ["intermediate", "expert"],
        "jobType": ["fixed", "hourly"],
        "clientPaymentVerifiedOnly": bool(payment_verified_only),
        "maxJobAge": {"value": hours_val, "unit": "hours"},
    }


class ApifyUpworkClient:
    """REST-клиент для запуска Upwork-акторов на платформе Apify."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        actor_id: str | None = None,
    ):
        self.api_key = api_key if api_key is not None else config.APIFY_API_KEY
        self.base_url = (base_url or config.APIFY_API_URL).rstrip("/")
        self.actor_id = normalize_actor_id(actor_id or config.APIFY_UPWORK_ACTOR_ID)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "JobFilter/1.4",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        if self.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.api_key}"

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def run_actor_sync(
        self,
        query: str,
        results_wanted: int = 50,
        hours_old: int = 24,
        payment_verified_only: bool | None = None,
        actor_id: str | None = None,
        timeout: int = 120,
    ) -> list[dict[str, Any]]:
        """
        Синхронно запускает актор Upwork через /acts/{actorId}/run-sync-get-dataset-items
        и возвращает список карточек из датасета. При ошибке 402/403/404 пробует резервные акторы.
        """
        verified_only = (
            config.UPWORK_PAYMENT_VERIFIED_ONLY
            if payment_verified_only is None
            else bool(payment_verified_only)
        )
        primary_actor = normalize_actor_id(actor_id or self.actor_id)
        candidates = [primary_actor]
        for fb in FALLBACK_UPWORK_ACTORS:
            if fb not in candidates:
                candidates.append(fb)

        last_exc: Exception | None = None
        for idx, act_id in enumerate(candidates):
            payload = _build_actor_input(
                actor_id=act_id,
                query=query,
                results_wanted=results_wanted,
                hours_old=hours_old,
                payment_verified_only=verified_only,
            )
            url = f"{self.base_url}/acts/{act_id}/run-sync-get-dataset-items"
            params = {
                "token": self.api_key,
                "clean": "true",
                "format": "json",
            }
            try:
                resp = self.session.post(url, params=params, json=payload, timeout=timeout)
                if resp.status_code in (200, 201):
                    data = resp.json()
                    if isinstance(data, list):
                        return data
                    if isinstance(data, dict) and isinstance(data.get("items"), list):
                        return data["items"]
                    if isinstance(data, dict) and isinstance(data.get("data"), list):
                        return data["data"]
                    return []

                # Если токен неверный (401) — нет смысла перебирать другие акторы
                if resp.status_code == 401:
                    resp.raise_for_status()

                # Если актор платный по подписке (402/403) или не найден (404), пробуем следующий
                err_detail = resp.text[:250] if resp.text else f"HTTP {resp.status_code}"
                logger.warning(
                    "Актор Apify '%s' вернул статус %s (%s). %s",
                    act_id,
                    resp.status_code,
                    err_detail,
                    "Пробуем резервный актор..." if idx + 1 < len(candidates) else "Резервных акторов больше нет.",
                )
                resp.raise_for_status()
            except Exception as e:
                last_exc = e
                if isinstance(e, requests.HTTPError) and e.response is not None and e.response.status_code == 401:
                    raise
                if idx + 1 < len(candidates):
                    continue
                raise

        if last_exc:
            raise last_exc
        return []


def _parse_upwork_date(val: Any, now: datetime | None = None) -> datetime | None:
    """Разбирает как ISO-даты, так и относительные строки Upwork ('15 minutes ago', '2 hours ago')."""
    if not val:
        return None
    ref_now = now or datetime.now(timezone.utc)
    val_str = str(val).strip()
    if not val_str:
        return None

    low = val_str.lower()
    if low in ("just now", "moments ago", "now"):
        return ref_now
    if low == "yesterday":
        return ref_now - timedelta(days=1)

    rel_match = re.search(
        r"(\d+)\s*(second|sec|minute|min|hour|hr|day|week|month)s?\s*ago",
        low,
    )
    if rel_match:
        num = int(rel_match.group(1))
        unit = rel_match.group(2)
        if unit.startswith("sec"):
            return ref_now - timedelta(seconds=num)
        if unit.startswith("min"):
            return ref_now - timedelta(minutes=num)
        if unit.startswith(("hour", "hr")):
            return ref_now - timedelta(hours=num)
        if unit.startswith("day"):
            return ref_now - timedelta(days=num)
        if unit.startswith("week"):
            return ref_now - timedelta(weeks=num)
        if unit.startswith("month"):
            return ref_now - timedelta(days=num * 30)

    try:
        clean_iso = val_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        pass

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(val_str, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None


def _extract_job_id(item: dict[str, Any]) -> str | None:
    """Извлекает стабильный идентификатор вакансии Upwork и добавляет префикс uw-."""
    for key in ("ciphertext", "id", "subId", "jobId", "uid"):
        raw = item.get(key)
        if raw and str(raw).strip():
            clean = str(raw).strip().lstrip("~")
            return f"uw-{clean}"

    for url_key in ("jobUrl", "link", "url"):
        u = str(item.get(url_key) or "").strip()
        if u:
            m = re.search(r"~([0-9a-zA-Z]+)", u)
            if m:
                return f"uw-{m.group(1)}"
    return None


def _extract_job_url(item: dict[str, Any], job_key: str) -> str:
    for url_key in ("jobUrl", "link", "url"):
        u = str(item.get(url_key) or "").strip()
        if u.startswith("http"):
            return u
    raw_id = job_key.removeprefix("uw-")
    return f"https://www.upwork.com/jobs/~{raw_id}"


def _format_upwork_salary(item: dict[str, Any]) -> str | None:
    """Форматирует почасовую ставку (Hourly) или фиксированный бюджет (Fixed-price) Upwork."""
    # 0. Формат blackfalcondata: hourlyBudgetMin / hourlyBudgetMax / budgetAmount
    hb_min = item.get("hourlyBudgetMin")
    hb_max = item.get("hourlyBudgetMax")
    if hb_min or hb_max:
        if hb_min and hb_max:
            return f"${float(hb_min):,.0f} - ${float(hb_max):,.0f}/hr (Hourly)"
        if hb_min:
            return f"от ${float(hb_min):,.0f}/hr (Hourly)"
        if hb_max:
            return f"до ${float(hb_max):,.0f}/hr (Hourly)"

    b_amount = item.get("budgetAmount")
    if isinstance(b_amount, (int, float)) and b_amount > 0:
        return f"${float(b_amount):,.0f} (Fixed-price)"

    # 1. Формат omkarcloud: hourly_rate: {"min": 20, "max": 60, "currency": "USD"}
    hr = item.get("hourly_rate") or item.get("hourlyRate")
    if isinstance(hr, dict):
        h_min = hr.get("min")
        h_max = hr.get("max")
        if h_min and h_max:
            return f"${float(h_min):,.0f} - ${float(h_max):,.0f}/hr (Hourly)"
        if h_min:
            return f"от ${float(h_min):,.0f}/hr (Hourly)"
        if h_max:
            return f"до ${float(h_max):,.0f}/hr (Hourly)"

    # 2. Формат neatrat / upwork-vibe: rate: "$20.00 - $40.00" или {"type": "hourly", "min": 25, "max": 50}
    rate = item.get("rate")
    if isinstance(rate, dict):
        r_min = rate.get("min")
        r_max = rate.get("max")
        if r_min and r_max:
            return f"${float(r_min):,.0f} - ${float(r_max):,.0f}/hr (Hourly)"
        if r_min:
            return f"${float(r_min):,.0f}/hr"
    elif isinstance(rate, str) and rate.strip():
        r_str = rate.strip()
        if "/hr" not in r_str.lower():
            return f"{r_str}/hr (Hourly)"
        return r_str

    # 3. Фиксированный бюджет: budget: 1500 или "$1,500" или {"amount": 1500}
    budget = item.get("budget") or item.get("amount")
    if isinstance(budget, dict):
        b_amt = budget.get("amount") or budget.get("max") or budget.get("min")
        if b_amt:
            try:
                return f"${float(b_amt):,.0f} (Fixed-price)"
            except (ValueError, TypeError):
                return f"{b_amt} (Fixed-price)"
    elif isinstance(budget, (int, float)) and budget > 0:
        return f"${float(budget):,.0f} (Fixed-price)"
    elif isinstance(budget, str) and budget.strip():
        b_str = budget.strip()
        try:
            num = float(b_str.replace("$", "").replace(",", ""))
            if num > 0:
                return f"${num:,.0f} (Fixed-price)"
        except ValueError:
            return f"{b_str} (Fixed-price)"

    return None


def _extract_client_info(item: dict[str, Any]) -> dict[str, Any]:
    """Извлекает нормализованные данные о клиенте Upwork (страна, траты, рейтинг, верификация)."""
    client = item.get("client") if isinstance(item.get("client"), dict) else {}
    loc = client.get("location") if isinstance(client.get("location"), dict) else {}
    stats = client.get("stats") if isinstance(client.get("stats"), dict) else {}

    country = (
        loc.get("country")
        or client.get("country")
        or item.get("clientCountry")
        or item.get("client_location")
        or ""
    )
    city = loc.get("city") or client.get("city") or ""

    verified = client.get("paymentVerified")
    if verified is None:
        verified = client.get("payment_verified")
    if verified is None:
        verified = item.get("paymentVerified") or item.get("clientPaymentVerified")

    raw_spent = (
        stats.get("totalSpent")
        or stats.get("total_spent")
        or client.get("totalSpent")
        or client.get("total_spent")
        or item.get("clientTotalSpent")
    )
    if isinstance(raw_spent, dict):
        raw_spent = raw_spent.get("amount")
    spent_val: float | None = None
    if raw_spent is not None:
        try:
            spent_val = float(str(raw_spent).replace("$", "").replace(",", "").strip())
        except (ValueError, TypeError):
            spent_val = None

    rating = stats.get("rating") or client.get("rating") or item.get("clientRating")
    company_name = client.get("company_name") or client.get("companyName") or item.get("company")

    return {
        "company_name": str(company_name).strip() if company_name else "",
        "country": str(country).strip() if country else "",
        "city": str(city).strip() if city else "",
        "payment_verified": bool(verified) if verified is not None else None,
        "total_spent": spent_val,
        "rating": rating,
    }


def _format_client_company_label(c_info: dict[str, Any]) -> str:
    """Формирует информативное имя заказчика для карточки в UI."""
    base = c_info["company_name"] or "Upwork Client"
    badges: list[str] = []
    if c_info["country"]:
        badges.append(c_info["country"])
    if c_info["total_spent"] is not None and c_info["total_spent"] > 0:
        spent = c_info["total_spent"]
        if spent >= 1000:
            badges.append(f"${spent / 1000:.0f}k+ spent")
        else:
            badges.append(f"${spent:.0f} spent")
    if c_info["payment_verified"]:
        badges.append("✓ Verified")

    if badges:
        return f"{base} ({' • '.join(badges)})"
    return base


def _extract_skills_list(item: dict[str, Any]) -> list[str]:
    raw_skills = item.get("skills") or item.get("tags") or item.get("ontologySkills") or []
    skills: list[str] = []
    if isinstance(raw_skills, list):
        for s in raw_skills:
            if isinstance(s, dict):
                name = s.get("name") or s.get("prettyName") or s.get("label")
                if name:
                    skills.append(str(name).strip())
            elif s and str(s).strip():
                skills.append(str(s).strip())
    return skills


def _matches_target_location(target_location: str, client_country: str, preferred_loc: str) -> bool:
    """Проверяет, подходит ли карточка под выбранный пользователем макрорегион в фильтре Upwork."""
    loc_norm = (target_location or "Worldwide").strip().lower()
    if not loc_norm or loc_norm in ("worldwide", "remote", "global", "anywhere"):
        return True

    combined = f"{client_country} {preferred_loc}".strip().lower()
    if not combined:
        # Если страна заказчика не указана в карточке, не отбрасываем глобальный заказ
        return True

    if loc_norm in ("emea",):
        return any(c in combined for c in EMEA_COUNTRIES) or "emea" in combined or "europe" in combined or "worldwide" in combined
    if loc_norm in ("europe", "european union", "eu"):
        return any(c in combined for c in EUROPE_COUNTRIES) or "europe" in combined or "worldwide" in combined
    if loc_norm in ("united states", "usa", "us"):
        return any(w in combined for w in ("united states", "usa", "u.s.", "america"))
    if loc_norm in ("united kingdom", "uk", "gb"):
        return any(w in combined for w in ("united kingdom", "uk", "great britain", "england"))

    return loc_norm in combined


def _items_to_dataframe(
    items: list[dict[str, Any]],
    target_location: str = "Worldwide",
    results_wanted: int = 50,
    hours_old: int = 24,
    processed_ids: set[str] | None = None,
) -> pd.DataFrame:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=hours_old) if hours_old and hours_old > 0 else None

    rows: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if len(rows) >= results_wanted:
            break

        job_key = _extract_job_id(item)
        if not job_key:
            continue

        if processed_ids and job_key in processed_ids:
            continue

        raw_date = (
            item.get("publishTime")
            or item.get("createTime")
            or item.get("published_at")
            or item.get("created_at")
            or item.get("postedOn")
            or item.get("postedDate")
            or item.get("createdDateTime")
            or item.get("date_posted")
        )
        pub_dt = _parse_upwork_date(raw_date, now=now)
        if cutoff and pub_dt and pub_dt < cutoff:
            continue

        c_info = _extract_client_info(item)
        pref_loc = str(
            item.get("preferredLocation")
            or item.get("candidateLocation")
            or item.get("locationRestrictions")
            or ""
        ).strip()

        if not _matches_target_location(target_location, c_info["country"], pref_loc):
            continue

        title = str(item.get("title") or "Upwork Contract").strip()
        job_url = _extract_job_url(item, job_key)
        company = _format_client_company_label(c_info)
        salary = _format_upwork_salary(item)

        if pref_loc:
            loc_display = f"Worldwide (Preferred: {pref_loc})"
        elif c_info["country"]:
            loc_display = f"Worldwide (Client: {c_info['country']})"
        else:
            loc_display = "Worldwide"

        exp_level = str(
            item.get("experienceLevel")
            or item.get("experience_level")
            or item.get("tier")
            or "Expert"
        ).strip()

        contract_type = str(
            item.get("contractType")
            or item.get("job_type")
            or item.get("jobType")
            or "contract"
        ).strip()

        skills = _extract_skills_list(item)
        base_desc = str(item.get("description") or item.get("snippet") or "").strip()

        # Дополняем текст описания структурированным блоком метаданных контракта для LLM и поиска по ключевым словам
        meta_lines: list[str] = ["", "--- Upwork Contract Metadata ---"]
        meta_lines.append(f"Contract Type: {contract_type}")
        if salary:
            meta_lines.append(f"Budget / Rate: {salary}")
        meta_lines.append(f"Experience Level: {exp_level}")
        if item.get("project_length") or item.get("duration") or item.get("engagementDuration"):
            meta_lines.append(
                f"Project Duration: {item.get('project_length') or item.get('duration') or item.get('engagementDuration')}"
            )
        if item.get("weekly_hours") or item.get("workload") or item.get("engagementType"):
            meta_lines.append(
                f"Weekly Hours: {item.get('weekly_hours') or item.get('workload') or item.get('engagementType')}"
            )
        if skills:
            meta_lines.append(f"Required Skills: {', '.join(skills)}")
        if c_info["country"]:
            meta_lines.append(f"Client Country: {c_info['country']}")
        if c_info["payment_verified"] is not None:
            meta_lines.append(f"Client Payment Verified: {'Yes' if c_info['payment_verified'] else 'No'}")
        if c_info["total_spent"] is not None:
            meta_lines.append(f"Client Total Spent: ${c_info['total_spent']:,.0f}")
        if item.get("proposals") or item.get("totalApplicants") is not None:
            meta_lines.append(f"Proposals: {item.get('proposals') or item.get('totalApplicants')}")
        meta_lines.append("Remote Eligibility: Worldwide Remote (B2B / Freelance Contract via Upwork)")

        full_desc = f"{base_desc}\n" + "\n".join(meta_lines) if base_desc else "\n".join(meta_lines).strip()

        rows.append({
            "id": job_key,
            "site": "upwork",
            "job_url": job_url,
            "job_url_direct": job_url,
            "title": title,
            "company": company,
            "location": loc_display,
            "date_posted": pub_dt.strftime("%Y-%m-%d") if pub_dt else now.strftime("%Y-%m-%d"),
            "salary": salary,
            "description": full_desc,
            "is_remote": True,
            "job_level": exp_level,
            "job_type": contract_type.lower(),
        })

    return pd.DataFrame(rows, columns=DF_COLS)


def scrape_upwork(
    term: str,
    location: str = "Worldwide",
    results_wanted: int = 50,
    hours_old: int = 24,
    client: ApifyUpworkClient | None = None,
    processed_ids: set[str] | None = None,
) -> pd.DataFrame:
    """
    Запускает поиск заказов Upwork через Apify Actor API и возвращает DataFrame в формате JobFilter.
    """
    client = client or ApifyUpworkClient()
    if not client.is_configured():
        msg = "APIFY_API_KEY не установлен. Укажите токен Apify в файле .env (APIFY_API_KEY=...)."
        logger.warning(msg)
        df_empty = pd.DataFrame(columns=DF_COLS)
        df_empty.attrs["errors"] = {"upwork": msg}
        return df_empty

    clean_term = re.sub(r"\bremote\b", "", term or "", flags=re.IGNORECASE).strip() or term

    try:
        items = client.run_actor_sync(
            query=clean_term,
            results_wanted=results_wanted,
            hours_old=hours_old,
        )
    except Exception as e:
        err_msg = f"Ошибка запроса к Apify Upwork Actor ({client.actor_id}): {e}"
        logger.error(err_msg)
        df_empty = pd.DataFrame(columns=DF_COLS)
        df_empty.attrs["errors"] = {"upwork": err_msg}
        return df_empty

    return _items_to_dataframe(
        items=items,
        target_location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
        processed_ids=processed_ids,
    )

