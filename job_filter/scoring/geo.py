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
    job_location: str | None = None,
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

    # Очищаем ограничения локации от предложений LLM вида "Ineligible for remote from Georgia, Tbilisi"
    clean_restrictions = [
        re.sub(r"\b(?:ineligible|not eligible|restricted|cannot work)\s+(?:for|from|to)\b.*", "", r, flags=re.IGNORECASE).strip()
        for r in enrichment.location_restrictions
    ]
    clean_restrictions = [r for r in clean_restrictions if r]
    restrictions_joined = " | ".join(clean_restrictions).lower()
    remote_low = (enrichment.remote_policy_detail or "").lower()
    fit_summary_low = ((enrichment.resume_fit.summary if enrichment.resume_fit else "") or "").lower()

    # Собираем только текст работодателя (НЕ включаем комментарии LLM о кандидате)
    loc_components = [
        title,
        job_location or "",
        restrictions_joined,
        remote_low,
        " ".join(enrichment.work_authorization.eligible_regions).lower(),
        (enrichment.relocation_benefits_detail or "").lower(),
    ]
    loc_text = " | ".join(filter(None, loc_components))
    full_lower = (loc_text + "\n" + (description or "")[:3000]).lower()

    has_relocation = (enrichment.relocation_assistance == "yes") or (
        enrichment.work_authorization.sponsorship == "yes"
    ) or any(
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

    # 3. Проверка глобальной удалёнки (Worldwide / Anywhere / Global Remote)
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

    # 4. Проверка жестких страновых локов: США (US)
    us_lock_patterns = [
        r"remote within the united states",
        r"must live in.*united states",
        r"us citizenship required",
        r"us work authorization required",
        r"united states only",
        r"\bus only\b",
        r"\bu\.s\. only\b",
        r"\bus residents?\s+only\b",
        r"\bu\.s\. residents?\s+only\b",
        r"based in the us\b",
        r"based in the united states\b",
        r"must (?:reside|live|be based|be located) in (?:the )?(?:us|u\.s\.|united states)\b",
        r"authorized to work in the (?:us|united states)",
        r"eligible to work in the (?:us|united states)",
        r"work authorization in the (?:us|united states)",
        r"401\(k\)",
    ]

    is_us_location = False
    jl_clean = (job_location or "").strip().lower()
    if jl_clean:
        if re.search(r"\b(usa|united states|u\.s\.a\.|u\.s\.|us)\b", jl_clean):
            is_us_location = True
        elif re.search(r",\s*[a-z]{2}\b", jl_clean):
            is_us_location = True

    is_us_restr = bool(
        re.search(r"\b(usa|united states|u\.s\.a\.|u\.s\.|us only|united states only)\b", restrictions_joined)
        or re.search(r",\s*[a-z]{2}\b", restrictions_joined)
    )

    is_us_locked = (
        any(re.search(pat, full_lower) for pat in us_lock_patterns)
        or is_us_location
        or is_us_restr
    )

    if is_us_locked and not is_true_global:
        if can_consider_relocation:
            return True, "Tier 2B: Relocation Opportunity (US)", None
        if reject_single_country:
            return False, "Rejected: US-only", "us_only_lock"

    # 5. Проверка других единичных стран (UK, Испания, Польша, Мексика, Аргентина, Индия и др.)
    single_country_names = (
        "uk", "united kingdom", "great britain", "england", "london",
        "spain", "bulgaria", "poland", "germany", "france", "italy",
        "romania", "ukraine", "portugal", "netherlands", "ireland",
        "hungary", "czech", "austria", "switzerland", "belgium", "sweden",
        "norway", "finland", "denmark", "greece", "lithuania", "latvia", "estonia",
        "canada", "australia", "mexico", "argentina", "brazil", "colombia", "chile",
        "india", "nepal", "pakistan", "philippines", "singapore", "japan", "south korea",
        "israel", "turkey", "egypt", "south africa", "latam",
    )

    has_broad_emea = any(
        w in restrictions_joined or w in jl_clean
        for w in ("emea", "europe", "cet", "utc+", "gmt+")
    )

    # Не считаем за лок, если это список из нескольких стран, включающий Грузию
    is_multi_country_with_georgia = (
        "georgia" in restrictions_joined and len(clean_restrictions) > 1
    ) or ("georgia" in jl_clean and ("," in jl_clean or "europe" in jl_clean))

    if not is_multi_country_with_georgia:
        for country_name in single_country_names:
            c_pat = (
                rf"\b{re.escape(country_name)}(?:\s+only|-based|\s+residents?\s+only)\b|"
                rf"\b(?:within|across)\s+(?:the\s+)?{re.escape(country_name)}\b|"
                rf"\bmust (?:reside|live|be based|be located) in (?:the )?{re.escape(country_name)}\b"
            )
            has_direct_country_loc = bool(jl_clean and re.search(rf"\b{re.escape(country_name)}\b", jl_clean))

            if re.search(c_pat, f"{restrictions_joined} | {remote_low}") or (
                has_direct_country_loc and not is_true_global and not has_broad_emea
            ):
                label = f"{country_name.upper()}-only" if country_name in ("uk", "us") else f"{country_name.title()}-only"
                if can_consider_relocation:
                    return True, f"Tier 2B: Relocation Opportunity ({label})", None
                if reject_single_country:
                    return False, f"Rejected: {label}", f"single_country_lock:{label}"

            if not has_broad_emea and not has_relocation:
                if re.search(rf"\b{re.escape(country_name)}\b", restrictions_joined):
                    label = f"{country_name.upper()}-only" if country_name in ("uk", "us") else f"{country_name.title()}-only"
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

    # 7. Формируем локальные ключевые слова для домашнего региона (Грузия / Кавказ / CEE) - БЕЗ EMEA!
    local_keywords = set()
    if "georgia" in current_loc:
        local_keywords.update(["georgia", "tbilisi", "batumi", "sakartvelo", "kutaisi"])
    for m in macro_regions:
        m_str = m.lower()
        if m_str in ("georgia", "tbilisi", "batumi", "sakartvelo", "kutaisi"):
            local_keywords.add(m_str)
        elif "caucasus" in m_str:
            local_keywords.update(["caucasus", "south caucasus", "transcaucasia"])
        elif "eastern europe" in m_str or m_str == "cee":
            local_keywords.update(["eastern europe", "cee", "central and eastern europe"])

    is_local_match = False
    if not is_us_locked:
        desc_clean = (description or "").lower()
        # Поиск совпадений в restrictions_joined (очищенном от ineligibility)
        has_restr_local = any(re.search(rf"\b{re.escape(kw)}\b", restrictions_joined) for kw in local_keywords)
        # Поиск совпадений в описании вакансии от работодателя
        has_desc_local = any(
            re.search(rf"\b{re.escape(kw)}\b", desc_clean)
            for kw in ("tbilisi", "batumi", "sakartvelo", "kutaisi", "remote in georgia", "hiring in georgia", "based in tbilisi")
        )
        is_local_match = has_restr_local or has_desc_local

    # 8. Приоритетное ранжирование по Tiers
    if is_local_match:
        return True, "Tier 1A: Local & Macro (Georgia)", None

    if is_true_global:
        return True, "Tier 1B: True Global Remote", None

    if has_broad_emea or any(w in restrictions_joined or w in remote_low for w in ("emea", "europe", "cet", "utc")):
        return True, "Tier 2A: Broad EMEA / Compatible Timezone", None

    return True, "Tier 2A: EMEA / Remote", None
