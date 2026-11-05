"""Классификация географических ограничений и Tier вакансии (Tier 1A/1B, Tier 2A/2B, Rejected)."""
import re
from typing import Any

from job_filter.db.seed_data import DEFAULT_GEO_PREFERENCES
from job_filter.models.enrichment import JobEnrichment


def classify_geo_tier(
    title: str,
    description: str,
    enrichment: JobEnrichment,
    geo_preferences: dict[str, Any] | None = None,
) -> tuple[bool, str, str | None]:
    """
    Классифицирует вакансию по географическим правилам на основе предпочтений кандидата:
    - Tier 1A: Прямое совпадение с локацией кандидата (Грузия) или её макрорегионом (Кавказ, Eastern Europe/CEE).
    - Tier 1B: Настоящая глобальная удалёнка (Worldwide / Work from anywhere / Anywhere).
    - Tier 2A: Широкий макрорегион EMEA или подходящий часовой пояс (UTC±3h).
    - Tier 2B: Локация в другой стране, НО компания предоставляет релокацию / Visa Sponsorship.
    - Tier 3 (Rejected): Удалёнка строго внутри одной чужой страны без релокации (US-only, UK-only, EU-only etc.).
    """
    prefs = geo_preferences or DEFAULT_GEO_PREFERENCES
    current_loc = str(prefs.get("current_location", "Georgia")).lower()
    macro_regions = [str(r).strip().lower() for r in (prefs.get("allowed_macro_regions") or []) if str(r).strip()]
    allow_worldwide = prefs.get("allow_worldwide_remote", True)
    relo_policy = str(prefs.get("relocation_policy", "with_sponsorship_only"))
    reject_single_country = prefs.get("reject_unsupported_single_country", True)

    loc_text = " | ".join(
        filter(
            None,
            [
                title,
                " ".join(enrichment.location_restrictions),
                enrichment.remote_policy_detail or "",
                enrichment.work_authorization.summary or "",
                " ".join(enrichment.work_authorization.eligible_regions),
                enrichment.relocation_benefits_detail or "",
            ],
        )
    ).lower()

    full_lower = (loc_text + "\n" + (description or "")[:3000]).lower()
    restrictions_joined = " | ".join(enrichment.location_restrictions).lower()
    remote_low = (enrichment.remote_policy_detail or "").lower()
    fit_summary_low = ((enrichment.resume_fit.summary if enrichment.resume_fit else "") or "").lower()

    has_relocation = (enrichment.relocation_assistance == "yes") or any(
        kw in full_lower
        for kw in (
            "visa sponsorship available",
            "relocation package",
            "relocation assistance",
            "willing to sponsor",
            "visa support",
            "help with relocation",
            "relocation offered",
        )
    )
    can_consider_relocation = (relo_policy in ("with_sponsorship_only", "open_to_relocation")) and has_relocation

    # 1. Проверка жестких контрактных ограничений (W2-only, Inside IR35, запрет B2B)
    contract_locks = [
        (r"\bw-?2 only\b|\bno c2c\b|\bno corp-to-corp\b", "W2-only (No B2B/C2C)"),
        (r"\binside ir35\b", "UK Inside IR35"),
        (r"\bpaye only\b", "UK PAYE-only (No B2B)"),
        (r"\bno b2b\b|\bno contractors\b", "No B2B / Contractors"),
    ]
    for pat, label in contract_locks:
        if re.search(pat, full_lower):
            return False, f"Rejected: {label}", f"contract_lock:{label}"

    # 2. Проверка требования обязательного гражданства РФ или оформления по ТК РФ
    ru_lock_patterns = [
        r"оформление по тк рф",
        r"только рф",
        r"гражданство рф",
        r"на территории рф",
    ]
    for pat in ru_lock_patterns:
        if re.search(pat, full_lower):
            return False, "Rejected: Russia-only", "ru_only_lock"

    # 3. Формируем локальные ключевые слова для домашнего региона (Грузия / Кавказ / Восточная Европа)
    local_keywords = set(macro_regions)
    if "georgia" in current_loc or "georgia" in macro_regions:
        local_keywords.update(["georgia", "tbilisi", "batumi", "sakartvelo", "kutaisi"])
    if any("caucasus" in m for m in macro_regions):
        local_keywords.update(["caucasus", "south caucasus", "transcaucasia"])
    if any("eastern europe" in m or "cee" in m for m in macro_regions):
        local_keywords.update(["eastern europe", "cee", "central and eastern europe"])

    is_local_match = any(
        re.search(rf"\b{re.escape(kw)}\b", restrictions_joined) or re.search(rf"\b{re.escape(kw)}\b", remote_low)
        for kw in local_keywords
    ) or any(kw in full_lower for kw in ("remote in georgia", "based in georgia", "georgia remote"))

    # 4. Проверка глобальной удалёнки (Worldwide / Anywhere / Global Remote)
    is_true_global = allow_worldwide and any(
        kw in full_lower or kw in restrictions_joined
        for kw in (
            "work from anywhere",
            "remote worldwide",
            "worldwide remote",
            "global remote",
            "anywhere in the world",
            "100% remote worldwide",
            "any location",
            "no location restrictions",
        )
    )

    # 5. Проверка жестких страновых локов (US, UK, Германия, Польша, Испания и др.)
    us_lock_patterns = [
        r"remote within the united states",
        r"must live in.*united states",
        r"us citizenship required",
        r"us work authorization required",
        r"united states only",
        r"\bus only\b",
        r"based in the us\b",
    ]
    is_us_locked = any(re.search(pat, full_lower) for pat in us_lock_patterns)
    if is_us_locked:
        if can_consider_relocation:
            return True, "Tier 2B: Relocation Opportunity (US)", None
        if reject_single_country:
            return False, "Rejected: US-only", "us_only_lock"

    single_country_names = (
        "uk", "united kingdom", "great britain", "england", "london",
        "spain", "bulgaria", "poland", "germany", "france", "italy",
        "romania", "ukraine", "portugal", "netherlands", "ireland",
        "hungary", "czech", "austria", "switzerland", "belgium", "sweden",
        "norway", "finland", "denmark", "greece", "lithuania", "latvia", "estonia",
        "canada", "australia",
    )

    has_broad_emea = any(
        w in restrictions_joined
        for w in ("emea", "europe", "cet", "utc+", "gmt+", "global", "worldwide", "anywhere", "multi", "georgia")
    )

    for country_name in single_country_names:
        c_pat = (
            rf"\b{re.escape(country_name)}(?:\s+only|-based|\s+residents?\s+only)\b|"
            rf"\b(?:within|across)\s+(?:the\s+)?{re.escape(country_name)}\b|"
            rf"\bmust (?:reside|live|be based|be located) in (?:the )?{re.escape(country_name)}\b"
        )
        if re.search(c_pat, f"{restrictions_joined} | {remote_low}"):
            label = f"{country_name.upper()}-only" if country_name == "uk" else f"{country_name.title()}-only"
            if can_consider_relocation:
                return True, f"Tier 2B: Relocation Opportunity ({label})", None
            if reject_single_country:
                return False, f"Rejected: {label}", f"single_country_lock:{label}"

        if not has_broad_emea and not has_relocation:
            if re.search(rf"\b{re.escape(country_name)}\b", restrictions_joined):
                label = f"{country_name.upper()}-only" if country_name == "uk" else f"{country_name.title()}-only"
                if can_consider_relocation:
                    return True, f"Tier 2B: Relocation Opportunity ({label})", None
                if reject_single_country:
                    return False, f"Rejected: {label}", f"single_country_lock:{label}"

    if re.search(
        r"(?:требует|ограничена)\s+(?:проживания|базирования|локацией)\s+в\s+(?:великобритании|uk|испании|болгарии|польше|германии|франции|сша)",
        fit_summary_low,
    ):
        if can_consider_relocation:
            return True, "Tier 2B: Relocation Opportunity (Residency)", None
        if reject_single_country:
            return False, "Rejected: Single-country residency required", "single_country_lock:residency"

    # 6. Проверка языковых требований Native/C1 (German, French, Dutch)
    for lang in enrichment.required_languages:
        l_low = lang.lower()
        if any(fl in l_low for fl in ("german", "french", "spanish", "polish", "italian", "dutch")) and not any(
            a1 in l_low for a1 in ("a1", "a2", "basic", "b1", "b2")
        ):
            return False, f"Rejected: Language ({lang})", f"required_language:{lang}"

    # 7. Приоритетное ранжирование по Tiers
    if is_local_match:
        return True, "Tier 1A: Local & Macro (Georgia)", None

    if is_true_global:
        return True, "Tier 1B: True Global Remote", None

    if has_broad_emea or any(w in restrictions_joined for w in ("emea", "europe", "cet", "utc")):
        return True, "Tier 2A: Broad EMEA / Compatible Timezone", None

    return True, "Tier 2A: EMEA / Remote", None
