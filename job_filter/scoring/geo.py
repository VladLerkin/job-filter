"""Классификация географических ограничений и Tier вакансии (Tier 1A/1B, Tier 2A/2B, Rejected)."""
import re
from typing import Any

from job_filter.db.seed_data import DEFAULT_GEO_PREFERENCES
from job_filter.models.enrichment import JobEnrichment

# Словарь сопоставления названий иностранных государств и их вариантов написания
FOREIGN_COUNTRY_MAP: dict[str, str] = {
    # UK & Ireland
    "uk": "UK", "united kingdom": "UK", "great britain": "UK", "england": "UK",
    "scotland": "UK", "wales": "UK", "london": "UK", "ireland": "Ireland", "dublin": "Ireland",
    # France & Monaco
    "france": "France", "paris": "France", "lyon": "France", "marseille": "France",
    "toulouse": "France", "bordeaux": "France", "lille": "France", "nice": "France",
    "nantes": "France", "strasbourg": "France", "rennes": "France", "villeurbanne": "France",
    "grenoble": "France", "montpellier": "France", "monaco": "Monaco",
    # DACH & Benelux
    "germany": "Germany", "deutschland": "Germany", "berlin": "Germany", "munich": "Germany", "frankfurt": "Germany",
    "austria": "Austria", "vienna": "Austria", "switzerland": "Switzerland", "zurich": "Switzerland", "geneva": "Switzerland",
    "netherlands": "Netherlands", "holland": "Netherlands", "amsterdam": "Netherlands", "rotterdam": "Netherlands",
    "belgium": "Belgium", "brussels": "Belgium", "luxembourg": "Luxembourg",
    # Southern Europe
    "spain": "Spain", "madrid": "Spain", "barcelona": "Spain", "valencia": "Spain",
    "portugal": "Portugal", "lisbon": "Portugal", "porto": "Portugal",
    "italy": "Italy", "milan": "Italy", "rome": "Italy", "turin": "Italy",
    "greece": "Greece", "athens": "Greece", "cyprus": "Cyprus", "malta": "Malta",
    # Central & Eastern Europe
    "poland": "Poland", "warsaw": "Poland", "krakow": "Poland", "cracow": "Poland", "polska": "Poland",
    "czech": "Czechia", "czechia": "Czechia", "czech republic": "Czechia", "prague": "Czechia", "brno": "Czechia",
    "slovakia": "Slovakia", "bratislava": "Slovakia",
    "hungary": "Hungary", "budapest": "Hungary",
    "romania": "Romania", "bucharest": "Romania", "cluj": "Romania",
    "bulgaria": "Bulgaria", "sofia": "Bulgaria",
    "croatia": "Croatia", "zagreb": "Croatia", "serbia": "Serbia", "belgrade": "Serbia", "novi sad": "Serbia", "slovenia": "Slovenia",
    "estonia": "Estonia", "latvia": "Latvia", "lithuania": "Lithuania",
    "ukraine": "Ukraine", "kyiv": "Ukraine", "kiev": "Ukraine",
    "moldova": "Moldova", "russia": "Russia", "belarus": "Belarus", "montenegro": "Montenegro",
    # Nordics
    "sweden": "Sweden", "stockholm": "Sweden", "norway": "Norway", "oslo": "Norway",
    "finland": "Finland", "helsinki": "Finland", "denmark": "Denmark", "copenhagen": "Denmark",
    # Americas
    "canada": "Canada", "toronto": "Canada", "vancouver": "Canada", "montreal": "Canada",
    "mexico": "Mexico", "brazil": "Brazil", "são paulo": "Brazil", "sao paulo": "Brazil", "argentina": "Argentina",
    "colombia": "Colombia", "chile": "Chile", "costa rica": "Costa Rica", "uruguay": "Uruguay", "peru": "Peru",
    # Asia & Others
    "india": "India", "pakistan": "Pakistan", "nepal": "Nepal", "philippines": "Philippines",
    "singapore": "Singapore", "japan": "Japan", "tokyo": "Japan", "south korea": "South Korea", "seoul": "South Korea",
    "australia": "Australia", "sydney": "Australia", "melbourne": "Australia", "new zealand": "New Zealand", "israel": "Israel",
    "turkey": "Turkey", "türkiye": "Turkey", "istanbul": "Turkey", "egypt": "Egypt", "south africa": "South Africa",
    "uae": "UAE", "united arab emirates": "UAE", "dubai": "UAE", "saudi arabia": "Saudi Arabia",
    "sri lanka": "Sri Lanka", "tunisia": "Tunisia", "tanzania": "Tanzania", "morocco": "Morocco",
}


def classify_geo_tier(
    title: str,
    description: str,
    enrichment: JobEnrichment,
    geo_preferences: dict[str, Any] | None = None,
    job_location: str | None = None,
    is_remote: bool | int | None = None,
) -> tuple[bool, str, str | None]:
    """
    Классифицирует вакансию по географическим правилам на основе предпочтений кандидата:
    - Tier 1A: Прямое совпадение с локацией кандидата (Грузия) или её макрорегионом (Кавказ, Eastern Europe/CEE).
    - Tier 1B: Настоящая глобальная удалёнка (Worldwide / Work from anywhere / Anywhere).
    - Tier 2A: Широкий макрорегион EMEA или подходящий часовой пояс (UTC±3h).
    - Tier 2B: Локация в другой стране, НО компания предоставляет релокацию / Visa Sponsorship.
    - Tier 3 (Rejected): Удалёнка строго внутри закрытого пула чужих стран без релокации (US-only, UK-only, EU-only, Czechia/Slovakia/Hungary etc.).
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
    work_auth_summary_low = ((enrichment.work_authorization.summary if enrichment.work_authorization else "") or "").lower()
    eligible_regions_low = [
        r.strip().lower() for r in (enrichment.work_authorization.eligible_regions if enrichment.work_authorization else []) if r.strip()
    ]
    jl_clean = (job_location or "").strip().lower()
    desc_clean = (description or "").lower()

    # Собираем только текст работодателя (НЕ включаем комментарии LLM о кандидате)
    loc_components = [
        title,
        jl_clean,
        restrictions_joined,
        remote_low,
        " ".join(eligible_regions_low),
        (enrichment.relocation_benefits_detail or "").lower(),
    ]
    loc_text = " | ".join(filter(None, loc_components))
    full_lower = (loc_text + "\n" + desc_clean[:3000]).lower()

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
    if jl_clean in ("russia", "russia (russia)") and not can_consider_relocation:
        return False, "Rejected: Russia-only", "ru_only_lock"

    # 3. Проверка глобальной удалёнки (Worldwide / Anywhere / Global Remote)
    # Исключаем временные тревел-перки (work from anywhere up to 90 days/year)
    # и локализованные фразы (work from anywhere across Japan / in the UK)
    is_scoped_or_temp_wfa = bool(
        re.search(
            r"(?:work\s+from\s+anywhere|wfa|working\s+remotely\s+from\s+anywhere)\s+(?:for\s+up\s+to\s+|for\s+|up\s+to\s+)?\d+\s+(?:days|weeks|months)|"
            r"\d+\s+(?:days|weeks)\s+(?:of\s+)?(?:work\s+from\s+anywhere|wfa|working\s+abroad)|"
            r"up\s+to\s+\d+\s+(?:days|weeks)\s+(?:per\s+year|\/year|a\s+year)\s+(?:working\s+from\s+anywhere|abroad)|"
            r"(?:work\s+from\s+anywhere|can\s+work\s+from\s+anywhere)\s+(?:in|across|within)\s+(?:the\s+)?[a-z]+|"
            r"anywhere\s+(?:in|across|within)\s+(?:the\s+)?(?:uk|united kingdom|japan|brazil|us|usa|united states|germany|spain|poland|canada)|"
            r"(?:contract|policy)\s+with\s+work\s+from\s+anywhere",
            full_lower,
        )
    )

    global_hiring_keywords = (
        "remote worldwide",
        "worldwide remote",
        "global remote",
        "anywhere in the world",
        "100% remote worldwide",
        "work from anywhere in the world",
        "open to candidates worldwide",
        "no location restrictions",
    )
    has_unambiguous_global = any(
        kw in full_lower or kw in restrictions_joined
        for kw in global_hiring_keywords
    ) or any(
        r in ("worldwide", "global", "anywhere")
        for r in clean_restrictions
    )

    is_pure_wfa = (
        "work from anywhere" in full_lower or "work from anywhere" in restrictions_joined
    ) and not is_scoped_or_temp_wfa

    is_true_global = allow_worldwide and (has_unambiguous_global or is_pure_wfa)

    # Если в явных ограничениях локации указаны конкретные иностранные государства без Worldwide/Global,
    # это не глобальная удалёнка
    has_explicit_country_restriction = any(
        var in clean_restrictions or var in eligible_regions_low
        for var in FOREIGN_COUNTRY_MAP
    )
    if has_explicit_country_restriction and not any(r in ("worldwide", "global", "anywhere") for r in clean_restrictions):
        is_true_global = False

    # 4. Формируем локальные ключевые слова для домашнего региона (Грузия / Кавказ / CEE) - БЕЗ EMEA!
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

    has_restr_local = any(re.search(rf"\b{re.escape(kw)}\b", restrictions_joined) for kw in local_keywords)
    has_desc_local = any(
        re.search(rf"\b{re.escape(kw)}\b", desc_clean)
        for kw in ("tbilisi", "batumi", "sakartvelo", "kutaisi", "remote in georgia", "hiring in georgia", "based in tbilisi")
    )
    has_jl_local = any(re.search(rf"\b{re.escape(kw)}\b", jl_clean) for kw in local_keywords)
    is_local_match = has_restr_local or has_desc_local or has_jl_local

    # 5. Проверка языковых требований Native/C1/Fluent (German, French, Spanish, Portuguese, Japanese и др.)
    foreign_mandatory_languages = (
        "german", "french", "spanish", "polish", "italian", "dutch",
        "portuguese", "português", "japanese", "korean", "chinese", "mandarin",
        "swedish", "norwegian", "danish", "finnish", "hungarian", "czech", "slovak",
        "romanian", "greek", "turkish", "hebrew", "arabic",
    )
    for lang in enrichment.required_languages:
        l_low = lang.lower()
        if any(fl in l_low for fl in foreign_mandatory_languages) and not any(
            a1 in l_low for a1 in ("a1", "a2", "basic", "b1", "b2")
        ):
            return False, f"Rejected: Language ({lang})", f"required_language:{lang}"

    # 6. Проверка жестких страновых локов: США (US)
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

    # 6. Проверка регуляторного лока ЕС/ЕЭЗ (EU/EEA-only)
    eu_lock_patterns = [
        r"\beu\s+only\b",
        r"\beea\s+only\b",
        r"\beu/eea\s+only\b",
        r"\beu\s+residents?\s+only\b",
        r"\beu\s+citizenship\s+required\b",
        r"\beu\s+work\s+permit\s+required\b",
        r"must\s+(?:reside|live|be\s+based|be\s+located)\s+in\s+(?:the\s+)?(?:eu|eea|european\s+union)\b",
        r"remote\s+(?:within|across)\s+(?:the\s+)?(?:eu|eea|european\s+union)\b",
    ]
    is_eu_locked = (
        any(re.search(pat, restrictions_joined) for pat in eu_lock_patterns)
        or any(re.search(pat, remote_low) for pat in eu_lock_patterns)
        or any(re.search(pat, full_lower) for pat in eu_lock_patterns)
    )
    if is_eu_locked and not is_local_match and not is_true_global:
        if can_consider_relocation:
            return True, "Tier 2B: Relocation Opportunity (EU-only)", None
        if reject_single_country:
            return False, "Rejected: EU-only", "single_country_lock:EU-only"

    # 7. Проверка закрытого пула иностранных государств (Country Pool / Single Foreign Country Lock)
    detected_foreign_countries: dict[str, str] = {}

    # а) Проверка в ограничениях локации и разрешенных регионах
    for item in clean_restrictions + eligible_regions_low:
        item_l = item.lower()
        for var, canon in FOREIGN_COUNTRY_MAP.items():
            if re.search(rf"\b{re.escape(var)}\b", item_l):
                detected_foreign_countries[canon] = canon

    # б) Проверка в скобках поля локации (например: "europe (Czech Republic, Hungary, Slovakia)" или "Remote (Mexico)")
    jl_paren_matches = re.findall(r"\(([^)]+)\)", jl_clean)
    for p_text in jl_paren_matches:
        for var, canon in FOREIGN_COUNTRY_MAP.items():
            if re.search(rf"\b{re.escape(var)}\b", p_text):
                detected_foreign_countries[canon] = canon

    # в) Проверка в самой строке локации, если это не обобщенное название макрорегиона
    if jl_clean and not any(
        jl_clean == broad or jl_clean.startswith(f"{broad} -")
        for broad in ("europe", "emea", "remote", "remote emea", "remote europe")
    ):
        for var, canon in FOREIGN_COUNTRY_MAP.items():
            if re.search(rf"\b{re.escape(var)}\b", jl_clean):
                detected_foreign_countries[canon] = canon

    # г) Проверка в описании условий удаленки через маркерные фразы (remote from X, residents of X, X-only)
    for var, canon in FOREIGN_COUNTRY_MAP.items():
        c_pat = (
            rf"\b{re.escape(var)}(?:\s+only|-based|\s+residents?\s+only)\b|"
            rf"\b(?:within|across)\s+(?:the\s+)?{re.escape(var)}\b|"
            rf"\bmust (?:reside|live|be based|be located) in (?:the )?{re.escape(var)}\b|"
            rf"\b(?:remote|hiring)\s+from\s+(?:the\s+)?{re.escape(var)}\b"
        )
        if re.search(c_pat, f"{restrictions_joined} | {remote_low}"):
            detected_foreign_countries[canon] = canon

    if detected_foreign_countries and not is_local_match and not is_true_global:
        unique_countries = sorted(set(detected_foreign_countries.values()))
        if len(unique_countries) == 1:
            c_name = unique_countries[0]
            label = f"{c_name.upper()}-only" if c_name.lower() in ("uk", "us", "uae") else f"{c_name}-only"
            if can_consider_relocation:
                return True, f"Tier 2B: Relocation Opportunity ({label})", None
            if reject_single_country:
                return False, f"Rejected: {label}", f"single_country_lock:{label}"
        else:
            c_names = ", ".join(unique_countries)
            if can_consider_relocation:
                return True, f"Tier 2B: Relocation Opportunity ({c_names})", None
            if reject_single_country:
                return False, f"Rejected: Restricted countries ({c_names})", f"country_pool_lock:{c_names}"

    # 8. Проверка прямых вердиктов LLM о жестком страновом или региональном ограничении
    llm_rejection_patterns = [
        r"(?:строго\s+)?ограничена\s+(?:ремоутом|удаленкой|проживанием|базированием|локацией)\s+(?:из|в)\s+",
        r"недоступна\s+для\s+удаленки\s+из\s+грузии",
        r"ineligible\s+for\s+remote\s+from\s+georgia",
        r"restricted\s+to\s+(?:residents|tax\s+residents)\s+in\s+",
        r"strictly\s+restricted\s+to\s+",
    ]
    has_llm_lock = any(
        re.search(pat, fit_summary_low) or re.search(pat, work_auth_summary_low)
        for pat in llm_rejection_patterns
    )
    if (has_llm_lock or getattr(enrichment, "candidate_geo_eligibility", "unclear") == "no") and not is_local_match and not is_true_global:
        if can_consider_relocation:
            return True, "Tier 2B: Relocation Opportunity (Residency)", None
        if reject_single_country:
            return False, "Rejected: Single-country / regional residency required", "single_country_lock:residency"

    # 9. Проверка требований физического присутствия (On-site / Hybrid) в чужой стране
    hybrid_office_patterns = [
        r"\btélétravail\s+(?:partiel|à\s+hauteur\s+de|\d+%)",
        r"\b(?:locaux|bureau|office)\s+(?:à|in|en)\s+[a-z]+",
        r"\bhybrid\s+(?:work|model|role|office|policy|position|setup|schedule|environment)\b",
        r"\d+\s*[-–]\s*\d+\s+days?\s+(?:a|per|\/)\s*week\s+(?:in|from)\s+(?:the\s+)?office\b",
        r"\d+\s+days?\s+(?:a|per|\/)\s*week\s+(?:in|from)\s+(?:the\s+)?office\b",
        r"\b(?:in-?office|office-?based|on-?site|onsite)\s+(?:role|work|position|job)\b",
        r"\b(?:must|required to)\s+(?:work|be|come|attend)\s+(?:in|from)\s+(?:the\s+)?office\b",
        r"гибридный\s+(?:формат|график|офис)",
        r"\bpresencial\b",
    ]
    is_explicit_non_remote = (is_remote is False) or (is_remote == 0) or (is_remote == "0")
    has_hybrid_policy = any(
        re.search(pat, f"{remote_low} | {fit_summary_low} | {desc_clean[:2000]}")
        for pat in hybrid_office_patterns
    )

    if (is_explicit_non_remote or has_hybrid_policy) and not is_local_match and not is_true_global:
        target_label = (
            list(detected_foreign_countries.values())[0]
            if detected_foreign_countries
            else (jl_clean or "Abroad")
        )
        if can_consider_relocation:
            return True, f"Tier 2B: Relocation Opportunity (On-site/Hybrid in {target_label})", None
        return False, f"Rejected: On-site / Hybrid in {target_label}", f"onsite_abroad_lock:{target_label}"

    # 10. Приоритетное ранжирование по Tiers
    if is_local_match:
        return True, "Tier 1A: Local & Macro (Georgia)", None

    if is_true_global:
        return True, "Tier 1B: True Global Remote", None

    has_broad_emea = any(
        w in restrictions_joined or w in jl_clean or w in remote_low
        for w in ("emea", "europe", "cet", "utc", "gmt")
    )
    if has_broad_emea:
        return True, "Tier 2A: Broad EMEA / Compatible Timezone", None

    return True, "Tier 2A: EMEA / Remote", None
