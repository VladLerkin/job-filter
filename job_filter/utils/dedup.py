"""Многоуровневая детерминированная дедупликация вакансий (без LLM).

Уровни проверки:
1. Нормализованный ключ `title::company` (убирает пунктуацию, дефисы, `REF#...`,
   маркеры локаций/remote/гендера, суффиксы юрлиц `Inc.`, `LLC`, `Technologies` и т.п.).
2. Мягкое сравнение заголовков внутри одной компании (token Jaccard >= 0.80 при >= 3 токенах),
   ловит мелкие перефразирования и теги Hirify вроде `(Agentic AI)` vs `| REMOTE`.
3. Нормализованный `apply_url` (без UTM/source/ref-параметров).
4. Сходство текста описания по 4-граммам слов (Jaccard >= 0.80),
   ловит мульти-локации и прокси-агрегаторы с другим названием компании.
"""
from __future__ import annotations

import re
from typing import Iterable, Mapping, Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

# Суффиксы юрлиц и типовые «хвосты» в названиях компаний
_COMPANY_SUFFIX_RE = re.compile(
    r"(?:,?\s+(?:"
    r"inc\.?|incorporated|llc|l\.l\.c\.?|ltd\.?|limited|corp\.?|corporation|"
    r"gmbh|plc|co\.?|technologies|technology|"
    r"sp\.?\s*z\.?\s*o\.?\s*o\.?|s\.?a\.?|b\.?v\.?|a\.?g\.?|s\.?r\.?l\.?"
    r"))+$",
    re.IGNORECASE,
)

# Обезличенные / служебные названия компаний, по которым нельзя матчить дубли по компании
GENERIC_COMPANIES: frozenset[str] = frozenset({
    "",
    "hirify employer",
    "confidential",
    "unknown",
    "stealth",
    "stealth startup",
    "anonymous",
    "undisclosed",
    "upwork client",
})

# Трекерные query-параметры, которые нужно выкидывать при нормализации apply_url
_TRACKING_QUERY_PARAMS: frozenset[str] = frozenset({
    "source",
    "src",
    "ref",
    "referer",
    "referrer",
    "via",
    "campaign",
    "gh_src",
    "lever-source",
    "lever-origin",
    "fbclid",
    "gclid",
    "trk",
    "trackingid",
    "mc_cid",
    "mc_eid",
    "igshid",
})

# Скобочные блоки с шумом: гендерные маркеры, remote/hybrid, локации с Remote
_NOISE_PAREN_RE = re.compile(
    r"\(\s*(?:"
    r"[mfdxwh]\s*/\s*[mfdxwh](?:\s*/\s*[mfdxwh])?|"
    r"all\s+genders?|"
    r"(?:100%\s+|full(?:y)?\s+)?remote(?:\s*(?:eligible|only|work|first))?(?:\s*[-,|/]\s*[^)]{1,45})?|"
    r"hybrid(?:\s*[-,|/]\s*[^)]{1,45})?|"
    r"on-?site|"
    r"worldwide|global|emea|europe|eu|uk|us|usa|canada|india|brazil|germany|poland|spain|france|deu|"
    r"cdmx|buenos\s+aires|guadalajara|london|berlin|dubai"
    r")\s*\)",
    re.IGNORECASE,
)

# Хвосты вида `| REF#311040`, `| REMOTE`, `- Remote Work`, `— 100% Remote`
_TRAILING_REF_RE = re.compile(r"\s*[\|\-–—]?\s*\bref\s*#?\s*[a-z0-9_-]+\b", re.IGNORECASE)
_TRAILING_REMOTE_RE = re.compile(
    r"\s*[\|\-–—]\s*(?:100%\s+|full(?:y)?\s+)?remote(?:\s+(?:work|only|eligible|first))?\b.*$",
    re.IGNORECASE,
)

# Словарь сокращений для унификации заголовков
_TITLE_ABBREV_MAP: dict[str, str] = {
    "sr": "senior",
    "snr": "senior",
    "jr": "junior",
    "jnr": "junior",
    "eng": "engineer",
    "engr": "engineer",
    "dev": "developer",
    "sw": "software",
    "swe": "software engineer",
    "ml": "machine learning",
    "genai": "generative ai",
}

# Шумовые токены в заголовках, не несущие смысла о роли
_TITLE_NOISE_TOKENS: frozenset[str] = frozenset({
    "remote",
    "hybrid",
    "onsite",
    "work",
    "eligible",
    "role",
    "position",
    "job",
    "opening",
    "opportunity",
    "worldwide",
    "global",
    "all",
    "genders",
    "gender",
    "m",
    "w",
    "d",
    "f",
    "x",
    "h",
    "and",
    "the",
    "for",
    "with",
    "in",
    "at",
    "of",
    "to",
    "a",
    "an",
})

FUZZY_TITLE_JACCARD_THRESHOLD = 0.80
FUZZY_TITLE_MIN_TOKENS = 3
DESC_SHINGLE_SIZE = 4
DESC_MIN_WORDS = 25
DESC_JACCARD_THRESHOLD = 0.80

# Токены грейда и специализации: при мягком матче заголовков они не должны расходиться,
# чтобы не склеить `Software Developer` с `Staff Software Developer` или `Fullstack` с `Backend`.
_DISTINCT_ROLE_TOKENS: frozenset[str] = frozenset({
    "intern",
    "junior",
    "mid",
    "middle",
    "senior",
    "staff",
    "principal",
    "lead",
    "director",
    "manager",
    "head",
    "vp",
    "backend",
    "frontend",
    "fullstack",
    "mobile",
    "ios",
    "android",
    "qa",
    "sdet",
    "devops",
    "sre",
    "security",
})


def normalize_company(company: str | None) -> str:
    """Нормализует название компании: регистр, спецсимволы, суффиксы юрлиц."""
    if not company:
        return ""
    s = company.strip().lower()
    s = re.sub(r"[®™©]", "", s)
    s = re.sub(r"\s+", " ", s)
    # Убираем суффиксы (возможно несколько подряд, например `, Technologies, Inc.`)
    for _ in range(3):
        new_s = _COMPANY_SUFFIX_RE.sub("", s).strip(" ,.-")
        if new_s == s:
            break
        s = new_s
    s = re.sub(r"[^a-z0-9а-яё]+", " ", s, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", s).strip()


def is_generic_company(norm_company: str) -> bool:
    """Возвращает True, если компания обезличена (Hirify Employer, Confidential, Upwork Client...)."""
    if not norm_company or norm_company in GENERIC_COMPANIES:
        return True
    if norm_company.startswith("upwork client"):
        return True
    return False


def _clean_title_raw(title: str | None) -> str:
    if not title:
        return ""
    s = title.strip().lower()
    s = re.sub(r"[–—−]", "-", s)
    s = _TRAILING_REF_RE.sub("", s)
    s = _NOISE_PAREN_RE.sub(" ", s)
    s = _TRAILING_REMOTE_RE.sub("", s)
    # Унифицируем составные термины до токенизации
    s = re.sub(r"\bfull[\s\-]+stack\b", "fullstack", s)
    s = re.sub(r"\bback[\s\-]+end\b", "backend", s)
    s = re.sub(r"\bfront[\s\-]+end\b", "frontend", s)
    s = re.sub(r"\bgen[\s\-]+ai\b", "generative ai", s)
    s = re.sub(r"\bsr\.?\b", "senior", s)
    s = re.sub(r"\bjr\.?\b", "junior", s)
    return s


def title_tokens(title: str | None) -> frozenset[str]:
    """Возвращает множество нормализованных значимых токенов заголовка."""
    cleaned = _clean_title_raw(title)
    if not cleaned:
        return frozenset()
    raw_tokens = re.findall(r"[a-z0-9а-яё+#]+", cleaned, flags=re.IGNORECASE)
    result: set[str] = set()
    for tok in raw_tokens:
        t = tok.strip("+#") if tok not in ("c#", "c++", "f#") else tok
        if not t:
            continue
        expanded = _TITLE_ABBREV_MAP.get(t, t)
        for part in expanded.split():
            if part and part not in _TITLE_NOISE_TOKENS:
                result.add(part)
    return frozenset(result)


def normalize_title(title: str | None) -> str:
    """Нормализованная строка заголовка для точного сравнения (порядок слов сохраняется)."""
    cleaned = _clean_title_raw(title)
    if not cleaned:
        return ""
    raw_tokens = re.findall(r"[a-z0-9а-яё+#]+", cleaned, flags=re.IGNORECASE)
    parts: list[str] = []
    for tok in raw_tokens:
        t = tok.strip("+#") if tok not in ("c#", "c++", "f#") else tok
        if not t:
            continue
        expanded = _TITLE_ABBREV_MAP.get(t, t)
        for part in expanded.split():
            if part and part not in _TITLE_NOISE_TOKENS:
                parts.append(part)
    return " ".join(parts)


def normalized_title_company_key(title: str | None, company: str | None) -> str:
    """Возвращает нормализованный ключ 'norm_title::norm_company' или '' для обезличенных компаний."""
    nc = normalize_company(company)
    if is_generic_company(nc):
        return ""
    nt = normalize_title(title)
    if not nt:
        return ""
    return f"{nt}::{nc}"


def normalize_apply_url(url: str | None) -> str:
    """Нормализует ATS/apply URL, удаляя трекинговые query-параметры и trailing slash."""
    if not url:
        return ""
    raw = url.strip()
    if not raw or "://" not in raw:
        return ""
    try:
        parsed = urlparse(raw)
    except Exception:
        return ""
    host = (parsed.hostname or "").lower().strip(".")
    if not host:
        return ""
    if host.startswith("www."):
        host = host[4:]
    path = re.sub(r"/+$", "", parsed.path or "").lower()
    # Фильтруем трекерные query-параметры, сохраняя значимые (jobId, gh_jid и т.п.)
    kept_params = sorted(
        (k.lower(), v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=False)
        if not k.lower().startswith("utm_") and k.lower() not in _TRACKING_QUERY_PARAMS
    )
    query = urlencode(kept_params)
    # Не дедуплицируем по пустому корню сайта без пути и параметров (https://company.com/)
    if not path and not query:
        return ""
    return urlunparse(("https", host, path, "", query, ""))


def description_shingles(description: str | None, n: int = DESC_SHINGLE_SIZE) -> frozenset[str]:
    """Строит множество n-грамм слов описания для быстрого сравнения Jaccard."""
    if not description:
        return frozenset()
    words = re.findall(r"[a-z0-9а-яё]{3,}", description.lower())
    if len(words) < DESC_MIN_WORDS:
        return frozenset()
    return frozenset(" ".join(words[i : i + n]) for i in range(len(words) - n + 1))


class DeduplicationIndex:
    """In-memory индекс для 4-уровневой дедупликации вакансий без обращения к LLM."""

    def __init__(
        self,
        fuzzy_title_threshold: float = FUZZY_TITLE_JACCARD_THRESHOLD,
        desc_threshold: float = DESC_JACCARD_THRESHOLD,
    ) -> None:
        self.fuzzy_title_threshold = fuzzy_title_threshold
        self.desc_threshold = desc_threshold
        self._tc_keys: dict[str, str] = {}
        self._company_titles: dict[str, list[tuple[str, frozenset[str]]]] = {}
        self._apply_urls: dict[str, str] = {}
        self._desc_entries: list[tuple[str, int, frozenset[str]]] = []

    @classmethod
    def from_records(cls, records: Iterable[Mapping[str, Any]]) -> DeduplicationIndex:
        idx = cls()
        for rec in records:
            idx.add(
                job_id=str(rec["job_id"]),
                title=rec.get("title"),
                original_title=rec.get("original_title"),
                company=rec.get("company"),
                apply_url=rec.get("apply_url"),
                description=rec.get("description"),
            )
        return idx

    def add(
        self,
        job_id: str,
        title: str | None = None,
        company: str | None = None,
        apply_url: str | None = None,
        description: str | None = None,
        original_title: str | None = None,
    ) -> None:
        nc = normalize_company(company)
        if not is_generic_company(nc):
            seen_nt: set[str] = set()
            seen_toks: set[frozenset[str]] = set()
            for t_val in (title, original_title):
                if not t_val:
                    continue
                nt = normalize_title(t_val)
                if nt and nt not in seen_nt:
                    seen_nt.add(nt)
                    self._tc_keys.setdefault(f"{nt}::{nc}", job_id)
                toks = title_tokens(t_val)
                if len(toks) >= FUZZY_TITLE_MIN_TOKENS and toks not in seen_toks:
                    seen_toks.add(toks)
                    self._company_titles.setdefault(nc, []).append((job_id, toks))

        norm_url = normalize_apply_url(apply_url)
        if norm_url:
            self._apply_urls.setdefault(norm_url, job_id)

        sh = description_shingles(description)
        if sh:
            self._desc_entries.append((job_id, len(sh), sh))

    def find_pre_fetch_duplicate(
        self,
        title: str | None,
        company: str | None,
        apply_url: str | None = None,
        original_title: str | None = None,
    ) -> tuple[str, str] | None:
        """
        Проверяет дубль ДО загрузки описания карточки:
        1) Нормализованный `apply_url` (если уже известен).
        2) Нормализованный ключ `title::company` (по `title` и `original_title`).
        3) Мягкий матч заголовков внутри одной компании (token Jaccard >= 0.80).

        Возвращает `(original_job_id, match_reason)` или `None`.
        """
        norm_url = normalize_apply_url(apply_url)
        if norm_url and norm_url in self._apply_urls:
            return self._apply_urls[norm_url], "apply_url"

        nc = normalize_company(company)
        if not is_generic_company(nc):
            title_variants: list[tuple[str, str]] = []
            if title:
                title_variants.append((title, "norm_title_company"))
            if original_title and original_title.strip().lower() != (title or "").strip().lower():
                title_variants.append((original_title, "original_title"))

            for t_val, exact_reason in title_variants:
                nt = normalize_title(t_val)
                if nt:
                    tc_key = f"{nt}::{nc}"
                    if tc_key in self._tc_keys:
                        return self._tc_keys[tc_key], exact_reason

            candidates = self._company_titles.get(nc)
            if candidates:
                thr = self.fuzzy_title_threshold
                for t_val, _ in title_variants:
                    toks = title_tokens(t_val)
                    if len(toks) < FUZZY_TITLE_MIN_TOKENS:
                        continue
                    t_len = len(toks)
                    t_roles = toks & _DISTINCT_ROLE_TOKENS
                    for orig_id, orig_toks in candidates:
                        o_len = len(orig_toks)
                        # Быстрая отсечка по размерам множеств
                        if min(t_len, o_len) / max(t_len, o_len) < thr:
                            continue
                        if t_roles != (orig_toks & _DISTINCT_ROLE_TOKENS):
                            continue
                        inter = len(toks & orig_toks)
                        if inter == 0:
                            continue
                        jacc = inter / (t_len + o_len - inter)
                        if jacc >= thr:
                            return orig_id, "fuzzy_title"
        return None

    def find_post_fetch_duplicate(
        self,
        apply_url: str | None = None,
        description: str | None = None,
    ) -> tuple[str, str] | None:
        """
        Проверяет дубль ПОСЛЕ загрузки деталей карточки (до отправки в LLM):
        1) Нормализованный `apply_url`.
        2) Сходство описания по 4-граммам (Jaccard >= 0.80).

        Возвращает `(original_job_id, match_reason)` или `None`.
        """
        norm_url = normalize_apply_url(apply_url)
        if norm_url and norm_url in self._apply_urls:
            return self._apply_urls[norm_url], "apply_url"

        sh = description_shingles(description)
        if sh and self._desc_entries:
            s_len = len(sh)
            thr = self.desc_threshold
            for orig_id, o_len, orig_sh in self._desc_entries:
                # Быстрая отсечка по длине: если min/max < threshold, Jaccard не может быть >= threshold
                if (s_len if s_len < o_len else o_len) / (s_len if s_len > o_len else o_len) < thr:
                    continue
                inter = len(sh & orig_sh)
                if inter == 0:
                    continue
                jacc = inter / (s_len + o_len - inter)
                if jacc >= thr:
                    return orig_id, "description"
        return None
