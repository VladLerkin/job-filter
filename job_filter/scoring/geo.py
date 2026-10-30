"""Классификация географических ограничений и Tier вакансии (Tier 1 Global/Georgia, Tier 2 EMEA, Rejected)."""
import re

from job_filter.models.enrichment import JobEnrichment


def classify_geo_tier(
    title: str,
    description: str,
    enrichment: JobEnrichment,
) -> tuple[bool, str, str | None]:
    """
    Классифицирует вакансию по географическим правилам:
    - Отсекает жесткие локи на 1 страну (US-only, UK-only, Poland-only, Germany-only, RU-only и т.д. без релокации/B2B).
    - Определяет Tier 1 (Global / Georgia / Anywhere) или Tier 2 (EMEA / Multi-hub / Timezone / Relocation).
    """
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
    has_relocation = enrichment.relocation_assistance == "yes"

    has_broad_emea = any(
        w in restrictions_joined
        for w in ("emea", "europe", "cet", "utc+", "gmt+", "global", "worldwide", "anywhere", "multi", "georgia")
    )

    single_country_names = (
        "uk", "united kingdom", "great britain", "england", "london",
        "spain", "bulgaria", "poland", "germany", "france", "italy",
        "romania", "ukraine", "portugal", "netherlands", "ireland",
        "hungary", "czech", "austria", "switzerland", "belgium", "sweden",
        "norway", "finland", "denmark", "greece", "lithuania", "latvia", "estonia",
    )
    for country_name in single_country_names:
        if re.search(
            rf"\b{re.escape(country_name)}(?:\s+only|-based|\s+residents?\s+only)\b|\b(?:within|across)\s+(?:the\s+)?{re.escape(country_name)}\b",
            f"{restrictions_joined} | {remote_low}",
        ) and not has_relocation:
            label = f"{country_name.upper()}-only" if country_name == "uk" else f"{country_name.title()}-only"
            return False, f"Rejected: {label}", f"single_country_lock:{label}"

        if not has_broad_emea and not has_relocation:
            if re.search(rf"\b{re.escape(country_name)}\b", restrictions_joined):
                label = f"{country_name.upper()}-only" if country_name == "uk" else f"{country_name.title()}-only"
                return False, f"Rejected: {label}", f"single_country_lock:{label}"

    if re.search(
        r"(?:требует|ограничена)\s+(?:проживания|базирования|локацией)\s+в\s+(?:великобритании|uk|испании|болгарии|польше|германии|франции|сша)",
        fit_summary_low,
    ) and not has_relocation:
        return False, "Rejected: Single-country residency required", "single_country_lock:residency"

    # Если явно разрешены Georgia / Worldwide / Anywhere / Global B2B
    if any(
        kw in full_lower
        for kw in (
            "georgia",
            "tbilisi",
            "work from anywhere",
            "remote worldwide",
            "global remote",
            "anywhere in the world",
        )
    ):
        return True, "Tier 1: Global / Georgia", None

    # Проверка жестких запретов на работу из-за рубежа (US-only, UK-only без визы, single-country EU lock)
    us_lock_patterns = [
        r"remote within the united states",
        r"must live in.*united states",
        r"us citizenship required",
        r"us work authorization required",
        r"united states only",
        r"based in the us\b",
    ]
    for pat in us_lock_patterns:
        if re.search(pat, full_lower):
            return False, "Rejected: US-only", "us_only_lock"

    ru_lock_patterns = [
        r"оформление по тк рф",
        r"только рф",
        r"гражданство рф",
        r"на территории рф",
    ]
    for pat in ru_lock_patterns:
        if re.search(pat, full_lower):
            return False, "Rejected: Russia-only", "ru_only_lock"

    # Проверка жестких ограничений по типу контракта (против B2B / Contractor из Грузии)
    contract_locks = [
        (r"\bw-?2 only\b|\bno c2c\b|\bno corp-to-corp\b", "W2-only (No B2B/C2C)"),
        (r"\binside ir35\b", "UK Inside IR35"),
        (r"\bpaye only\b", "UK PAYE-only (No B2B)"),
        (r"\bno b2b\b|\bno contractors\b", "No B2B / Contractors"),
    ]
    for pat, label in contract_locks:
        if re.search(pat, full_lower):
            return False, f"Rejected: {label}", f"contract_lock:{label}"

    single_country_locks = [
        (r"\b(?:uk|united kingdom) only\b", "UK-only"),
        (r"\bmust (?:reside|live|be based|be located) in (?:the )?(?:uk|united kingdom)\b", "UK-only"),
        (r"\bsc eligible\b", "UK Security Clearance required"),
        (r"\bsecurity clearance\b", "Security Clearance required"),
        (r"\bpoland only\b|\bmust (?:reside|live|be based) in poland\b", "Poland-only"),
        (r"\bgermany only\b|\bmust (?:reside|live|be based) in germany\b", "Germany-only"),
        (r"\bfrance only\b|\bmust (?:reside|live|be based) in france\b", "France-only"),
        (r"\bspain only\b|\bmust (?:reside|live|be based) in spain\b", "Spain-only"),
        (r"\bitaly only\b|\bmust (?:reside|live|be based) in italy\b", "Italy-only"),
        (r"\bromania only\b|\bmust (?:reside|live|be based) in romania\b", "Romania-only"),
        (r"\bukraine only\b|\bmust (?:reside|live|be based) in ukraine\b", "Ukraine-only"),
    ]
    for pat, label in single_country_locks:
        if re.search(pat, full_lower) and not has_relocation:
            return False, f"Rejected: {label}", f"single_country_lock:{label}"

    # Если в заголовке/ограничениях жестко указан 1 город/страна без слова EMEA/Europe/Worldwide
    if not has_broad_emea and not has_relocation:
        if re.search(r"\b(?:uk|united kingdom|london|poland|germany|france|spain|italy|netherlands|ireland)\s+only\b", restrictions_joined):
            return False, f"Rejected: {enrichment.location_restrictions}", "single_country_restriction"

    # Проверка требования немецкого/французского/польского языка на уровне C1/Native
    for lang in enrichment.required_languages:
        l_low = lang.lower()
        if any(fl in l_low for fl in ("german", "french", "spanish", "polish", "italian", "dutch")) and not any(
            a1 in l_low for a1 in ("a1", "a2", "basic")
        ):
            return False, f"Rejected: Language ({lang})", f"required_language:{lang}"

    if any(w in restrictions_joined for w in ("worldwide", "global", "anywhere")):
        return True, "Tier 1: Global / Georgia", None

    return True, "Tier 2: EMEA / Multi-hub", None
