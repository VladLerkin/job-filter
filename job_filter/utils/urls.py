"""Чистые утилиты для работы с URL, доменами ATS и ключами компаний."""
import re
from urllib.parse import urlparse

KNOWN_MULTI_TENANT_ATS = (
    "icims.com",
    "cims.com",
    "myworkdayjobs.com",
    "workday.com",
    "taleo.net",
    "successfactors.com",
    "successfactors.eu",
    "greenhouse.io",
    "lever.co",
    "ashbyhq.com",
    "smartrecruiters.com",
    "workable.com",
    "breezy.hr",
    "bamboohr.com",
    "jobvite.com",
    "ultipro.com",
    "dayforcehcm.com",
    "brassring.com",
    "oraclecloud.com",
    "pageuppeople.com",
    "avature.net",
    "recruitee.com",
    "teamtailor.com",
    "personio.de",
    "personio.com",
)

CAPTCHA_AND_UTILITY_DOMAINS = (
    "hcaptcha.com",
    "recaptcha.net",
    "google.com",
    "gstatic.com",
    "cloudflare.com",
    "challenges.cloudflare.com",
    "arkoselabs.com",
    "geetest.com",
    "doubleclick.net",
    "googletagmanager.com",
)

SEARCH_AGGREGATOR_DOMAINS = (
    "linkedin.com",
    "hirify.me",
    "indeed.com",
    "glassdoor.com",
    "upwork.com",
)


def is_search_aggregator_domain(domain_or_url: str | None) -> bool:
    """Проверяет, является ли домен поисковым агрегатором (LinkedIn, Hirify, Indeed, Glassdoor, Upwork).
    Такие домены защищены от добавления в чёрный список, так как по ним ведётся поиск вакансий.
    """
    if not domain_or_url:
        return False
    host = extract_host(domain_or_url)
    if not host:
        return False
    if any(host == d or host.endswith("." + d) for d in SEARCH_AGGREGATOR_DOMAINS):
        return True
    if re.search(r"(^|\.)(linkedin|hirify|indeed|glassdoor|upwork)\.[a-z.]+$", host):
        return True
    return False


def is_utility_or_captcha_domain(domain_or_url: str | None) -> bool:
    """Проверяет, относится ли адрес к служебным сервисам капчи или трекинга, а не к ATS-бордам."""
    if not domain_or_url:
        return False
    dom = extract_root_domain(domain_or_url)
    if not dom:
        return False
    dom = dom.lower()
    return any(dom == u or dom.endswith("." + u) for u in CAPTCHA_AND_UTILITY_DOMAINS)


def normalize_company_key(company: str | None) -> str:
    if not company:
        return ""
    return re.sub(r"\s+", " ", company.strip().lower())


def extract_root_domain(url_or_domain: str | None) -> str | None:
    """Извлекает базовый домен ATS или сайта из URL или строки домена."""
    if not url_or_domain:
        return None
    raw = url_or_domain.strip()
    if not raw:
        return None
    if "://" not in raw:
        raw = "https://" + raw
    try:
        parsed = urlparse(raw)
        host = (parsed.hostname or "").lower().strip(".")
    except Exception:
        return None
    if not host:
        return None
    if host.startswith("www."):
        host = host[4:]

    for ats in KNOWN_MULTI_TENANT_ATS:
        if host == ats or host.endswith("." + ats):
            return ats

    parts = host.split(".")
    if len(parts) >= 3 and parts[-2] in ("co", "com", "org", "net", "gov") and len(parts[-1]) == 2:
        return ".".join(parts[-3:])
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host


# Домены, которые считаются одним и тем же ATS (бан одного = бан другого)
ATS_DOMAIN_ALIASES: dict[str, str] = {
    "cims.com": "icims.com",
    "icims.com": "cims.com",
}


def extract_host(url_or_domain: str | None) -> str:
    """Возвращает hostname без www. из URL или «голого» домена."""
    raw = (url_or_domain or "").strip()
    if not raw:
        return ""
    host = raw.lower()
    if "://" in raw or "/" in raw:
        try:
            host = (urlparse(raw if "://" in raw else "https://" + raw).hostname or "").lower().strip(".")
        except Exception:
            pass
    if host.startswith("www."):
        host = host[4:]
    return host


def find_domain_in_map(domain: str | None, bad_map: dict[str, str]) -> str | None:
    """Ищет домен (или его родительский домен) в словаре domain -> reason. Возвращает ключ словаря."""
    if not domain:
        return None
    low = domain.lower()
    if low in bad_map:
        return low
    for bad_dom in bad_map:
        if low.endswith("." + bad_dom):
            return bad_dom
    return None
