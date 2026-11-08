"""Интеграция со скиллом @job-application-tracker для синхронизации статусов откликов (Applied)."""
import json
import logging
import re
from typing import Any
from urllib.parse import quote

from job_filter import config
from job_filter.llm.agy_client import LLMError, extract_json_object, run_agy
from job_filter.utils.urls import normalize_company_key

logger = logging.getLogger(__name__)

VALID_APPLICATION_STAGES = ("applied", "confirmed", "interview", "rejected_by_company")

STAGE_PRIORITY = {
    "applied": 0,
    "confirmed": 1,
    "rejected_by_company": 2,
    "interview": 3,
}

TRACKER_OUTPUT_EXAMPLE = """{
  "summary": "Краткая сводка на русском: сколько компаний прислали подтверждение, сколько отказали и сколько позвали на интервью",
  "updates": [
    {
      "job_id": "li-4484586474",
      "company": "Teradata",
      "title": "Staff AI Engineer",
      "stage": "confirmed",
      "reason": "Получено автоматическое подтверждение отклика"
    },
    {
      "job_id": "hf-1345167",
      "company": "ITHAKA",
      "title": "Principal Software Engineer (Backend)",
      "stage": "rejected_by_company",
      "reason": "Отказ после скрининга резюме: выбрали кандидатов с более близким опытом"
    },
    {
      "job_id": "li-4472955260",
      "company": "Glia",
      "title": "Senior Software Engineer - Conversational AI",
      "stage": "interview",
      "reason": "Приглашение на 30-минутный HR-скрининг",
      "email_url": "https://mail.google.com/mail/u/0/#search/Glia",
      "email_subject": "Invitation to interview at Glia"
    }
  ]
}"""


def build_gmail_search_url(company: str | None, email_subject: str | None = None) -> str | None:
    """Формирует прямую ссылку на поиск письма в веб-интерфейсе Gmail по теме или названию компании."""
    subj = (email_subject or "").strip()
    comp = (company or "").strip()
    if subj:
        query = f'subject:"{subj}"'
    elif comp and comp.lower() not in ("unknown", "confidential"):
        query = f'"{comp}"'
    else:
        return None
    return f"https://mail.google.com/mail/u/0/#search/{quote(query)}"


def normalize_stage(raw_stage: str | None) -> str:
    """Приводит произвольное текстовое название этапа к одному из канонических значений."""
    s = (raw_stage or "").strip().lower()
    if s in VALID_APPLICATION_STAGES:
        return s
    if any(k in s for k in ("interview", "screen", "hr", "call", "invite", "интервью", "скрининг", "собеседован", "приглаш")):
        return "interview"
    if any(k in s for k in ("reject", "declin", "unfortunately", "not moving", "отказ", "отклон")):
        return "rejected_by_company"
    if any(k in s for k in ("confirm", "received", "acknowledg", "thank you for applying", "подтвержд", "получен")):
        return "confirmed"
    return "applied"


def build_gemini_tracker_prompt(
    applied_jobs: list[dict],
    skill_name: str = "@job-application-tracker",
) -> str:
    """Формирует готовый промпт для @job-application-tracker только по активным откликам (без уже отклонённых компаниями)."""
    skill_tag = (skill_name or "@job-application-tracker").strip()
    if not skill_tag.startswith("@") and not skill_tag.startswith("/"):
        skill_tag = f"@{skill_tag}"

    companies_map: dict[str, list[str]] = {}
    rejected_companies: list[str] = []

    for j in applied_jobs:
        comp = (j.get("company") or "Unknown").strip()
        if not comp or comp.lower() == "confidential":
            continue
        stage = (j.get("application_stage") or "applied").strip()
        if stage == "rejected_by_company":
            if comp not in rejected_companies:
                rejected_companies.append(comp)
            continue

        title = (j.get("title") or "").strip()
        companies_map.setdefault(comp, [])
        if title and title not in companies_map[comp]:
            companies_map[comp].append(title)

    # Убираем из списка уже отклонённых те компании, по которым есть другие ещё активные вакансии
    rejected_only = [c for c in rejected_companies if c not in companies_map]

    lines = []
    for idx, (comp, titles) in enumerate(companies_map.items(), start=1):
        titles_str = "; ".join(titles[:3])
        lines.append(f"{idx}. {comp}" + (f" ({titles_str})" if titles_str else ""))

    companies_block = "\n".join(lines) if lines else "(все отклики уже обработаны или список пуст)"
    skip_block = (
        f"\nНе включай в отчёт компании, по которым отказ уже занесён в базу: {', '.join(rejected_only)}.\n"
        if rejected_only
        else ""
    )

    return (
        f"{skill_tag} Проверь, пожалуйста, мои письма по откликам на вакансии и покажи подробную сводку:\n"
        f"1. Сколько и какие компании прислали подтверждение получения отклика (confirmed).\n"
        f"2. Сколько и какие компании отклонили вакансию (rejected_by_company) и по какой именно причине.\n"
        f"3. Сколько и какие компании пригласили на HR-скрининг, созвон или техническое интервью (interview).\n\n"
        f"Проверь статус по следующим активным откликам:\n"
        f"{companies_block}\n"
        f"{skip_block}\n"
        f"Для каждой найденной компании укажи: Название компании | Вакансия | Статус (confirmed / rejected_by_company / interview) | Причина отказа или детали приглашения на русском языке.\n"
        f"ВАЖНО: Если пришло приглашение на интервью или HR-скрининг (interview), обязательно укажи прямую ссылку на это письмо в Gmail (или точную тему письма Subject и email отправителя, либо ссылку на бронирование слота Calendly/Greenhouse из письма)."
    )


def build_llm_sync_prompt(
    applied_jobs: list[dict],
    report_text: str | None = None,
    skill_name: str = "@job-application-tracker",
) -> str:
    """Строит промпт для LLM (`agy` CLI), чтобы получить JSON со статусами по списку активных Applied-вакансий."""
    active_jobs = [
        j for j in applied_jobs
        if (j.get("application_stage") or "applied") != "rejected_by_company"
    ]
    compact_jobs = [
        {
            "job_id": j.get("job_id"),
            "company": j.get("company"),
            "title": j.get("title"),
            "date_posted": j.get("date_posted"),
            "current_stage": j.get("application_stage") or "applied",
        }
        for j in active_jobs
    ]
    jobs_json = json.dumps(compact_jobs, ensure_ascii=False, indent=2)

    if report_text and report_text.strip():
        return (
            "Ты — ИИ-ассистент трекера откликов на вакансии (Job Application Tracker).\n"
            "Ниже приведён отчёт о письмах от работодателей (из скилла @job-application-tracker / Gmail) "
            "и список вакансий кандидата со статусом 'applied' из базы Job Filter.\n\n"
            "Твоя задача:\n"
            "1. Сопоставить компании и вакансии из отчёта со списком Applied-вакансий из базы (по названию компании и/или должности).\n"
            "   Если в базе несколько вакансий одной и той же компании, а в отчёте не уточнена конкретная должность — верни обновления для всех подходящих job_id этой компании.\n"
            "2. Для каждой затронутой вакансии определить статус (`stage`):\n"
            "   - `confirmed`: компания прислала подтверждение получения резюме/отклика (и пока нет ни отказа, ни приглашения).\n"
            "   - `rejected_by_company`: компания прислала отказ. Обязательно укажи причину отказа на русском языке в поле `reason` (например: «Выбрали других кандидатов на этапе резюме», «Вакансия закрыта», «Не подошла локация / часовой пояс»).\n"
            "   - `interview`: компания пригласила на HR-скрининг, интервью, созвон или тестовое задание. В поле `reason` укажи детали приглашения на русском языке. Если в отчёте есть ссылка на письмо в Gmail или ссылка на запись (Calendly и т.п.) — передай её в `email_url`, а если указана тема письма — передай её в `email_subject`.\n"
            "3. Если для компании одновременно было письмо-подтверждение и позже письмо с отказом или приглашением на интервью — выбирай наиболее значимый актуальный статус (`interview` > `rejected_by_company` > `confirmed`).\n"
            "4. Сформировать общую краткую сводку на русском языке в поле `summary`.\n\n"
            f"Формат ответа — СТРОГО валидный JSON по образцу:\n{TRACKER_OUTPUT_EXAMPLE}\n\n"
            f"--- СПИСОК APPLIED ВАКАНСИЙ В БАЗЕ ---\n{jobs_json}\n--- КОНЕЦ СПИСКА ВАКАНСИЙ ---\n\n"
            f"--- ОТЧЁТ @job-application-tracker / ПИСЬМА ---\n{report_text.strip()}\n--- КОНЕЦ ОТЧЁТА ---"
        )

    skill_tag = (skill_name or "@job-application-tracker").strip()
    if not skill_tag.startswith("@") and not skill_tag.startswith("/"):
        skill_tag = f"@{skill_tag}"

    return (
        f"{skill_tag}\n"
        "Используй скилл job-application-tracker (или доступные инструменты проверки почты/откликов), "
        "чтобы проверить статус моих откликов по списку компаний ниже:\n"
        "- какие компании прислали подтверждение (`confirmed`),\n"
        "- какие отклонили вакансию (`rejected_by_company`) и по какой причине (`reason`),\n"
        "- какие пригласили на HR-скрининг или интервью (`interview`).\n\n"
        f"Верни ответ СТРОГО в формате JSON по образцу:\n{TRACKER_OUTPUT_EXAMPLE}\n\n"
        f"--- СПИСОК APPLIED ВАКАНСИЙ В БАЗЕ ---\n{jobs_json}\n--- КОНЕЦ СПИСКА ВАКАНСИЙ ---"
    )


def _company_tokens(name: str | None) -> str:
    if not name:
        return ""
    cleaned = re.sub(r"[^a-zA-Z0-9а-яА-ЯёЁ]+", " ", name.lower()).strip()
    # Убираем общие юридические суффиксы
    stop = {"inc", "llc", "ltd", "gmbh", "corp", "corporation", "co", "company", "group", "technologies", "technology", "software"}
    parts = [p for p in cleaned.split() if p not in stop]
    return " ".join(parts) if parts else cleaned


def match_updates_to_applied_jobs(
    raw_updates: list[dict[str, Any]],
    applied_jobs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Сопоставляет элементы updates из ответа LLM с конкретными вакансиями из applied_jobs."""
    jobs_by_id = {str(j["job_id"]): j for j in applied_jobs if j.get("job_id")}
    matched_by_job_id: dict[str, dict[str, Any]] = {}

    for upd in raw_updates:
        if not isinstance(upd, dict):
            continue
        stage = normalize_stage(upd.get("stage") or upd.get("status"))
        reason = (upd.get("reason") or upd.get("details") or upd.get("note") or "").strip() or None
        raw_email_url = (upd.get("email_url") or upd.get("link") or upd.get("url") or "").strip() or None
        email_subject = (upd.get("email_subject") or upd.get("subject") or "").strip() or None
        jid = str(upd.get("job_id") or "").strip()
        comp_raw = (upd.get("company") or "").strip()
        title_raw = (upd.get("title") or "").strip().lower()

        target_jobs: list[dict[str, Any]] = []
        if jid and jid in jobs_by_id:
            target_jobs.append(jobs_by_id[jid])
        elif comp_raw:
            upd_key = normalize_company_key(comp_raw)
            upd_tok = _company_tokens(comp_raw)
            candidates = []
            for job in applied_jobs:
                j_comp = job.get("company") or ""
                j_key = normalize_company_key(j_comp)
                j_tok = _company_tokens(j_comp)
                if not j_key or j_key == "confidential":
                    continue
                if j_key == upd_key or (j_tok and upd_tok and j_tok == upd_tok):
                    candidates.append(job)
                elif len(upd_tok) >= 4 and len(j_tok) >= 4 and (upd_tok in j_tok or j_tok in upd_tok):
                    candidates.append(job)

            if len(candidates) > 1 and title_raw:
                narrowed = [
                    c for c in candidates
                    if title_raw in (c.get("title") or "").lower() or (c.get("title") or "").lower() in title_raw
                ]
                target_jobs = narrowed if narrowed else candidates
            else:
                target_jobs = candidates

        for tj in target_jobs:
            t_id = str(tj["job_id"])
            resolved_url = raw_email_url
            if not resolved_url and (stage == "interview" or email_subject):
                resolved_url = build_gmail_search_url(tj.get("company") or comp_raw, email_subject)

            existing = matched_by_job_id.get(t_id)
            if existing:
                old_prio = STAGE_PRIORITY.get(existing["stage"], 0)
                new_prio = STAGE_PRIORITY.get(stage, 0)
                if new_prio > old_prio or (new_prio == old_prio and reason and not existing.get("reason")):
                    matched_by_job_id[t_id] = {
                        "job_id": t_id,
                        "company": tj.get("company"),
                        "title": tj.get("title"),
                        "stage": stage,
                        "reason": reason or existing.get("reason"),
                        "email_url": resolved_url or existing.get("email_url"),
                    }
            else:
                matched_by_job_id[t_id] = {
                    "job_id": t_id,
                    "company": tj.get("company"),
                    "title": tj.get("title"),
                    "stage": stage,
                    "reason": reason,
                    "email_url": resolved_url,
                }

    return list(matched_by_job_id.values())


def parse_tracker_report_heuristic(
    report_text: str,
    applied_jobs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Детерминированный парсер отчёта @job-application-tracker (фолбэк, если LLM недоступен или передан JSON/таблица)."""
    text = (report_text or "").strip()
    if not text:
        return {"summary": "", "updates": []}

    # 1. Пробуем распарсить как JSON, если пользователь вставил JSON
    try:
        obj = extract_json_object(text)
        if isinstance(obj.get("updates"), list):
            matched = match_updates_to_applied_jobs(obj["updates"], applied_jobs)
            return {
                "summary": obj.get("summary") or f"Сопоставлено вакансий из JSON: {len(matched)}",
                "updates": matched,
            }
    except Exception:
        pass

    # 2. Построчный разбор текста / Markdown-таблиц / списков с поиском названий компаний из applied_jobs
    raw_updates: list[dict[str, Any]] = []
    current_section_stage: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        low = line.lower()

        # Проверяем, не является ли строка заголовком секции ("Отказы:", "Rejections:", "Приглашения на интервью:", "Подтверждения:")
        if line.startswith("#") or line.endswith(":") or (len(line) < 70 and ("**" in line or line.isupper())):
            if any(w in low for w in ("interview", "screening", "hr", "интервью", "скрининг", "приглаш", "собеседован")):
                current_section_stage = "interview"
            elif any(w in low for w in ("reject", "declin", "отказ", "отклон")):
                current_section_stage = "rejected_by_company"
            elif any(w in low for w in ("confirm", "acknowledg", "received", "подтвержд", "получен")):
                current_section_stage = "confirmed"

        # Ищем упоминание любой компании из applied_jobs в строке
        for job in applied_jobs:
            comp = (job.get("company") or "").strip()
            if not comp or comp.lower() in ("unknown", "confidential") or len(comp) < 2:
                continue
            comp_tok = _company_tokens(comp)
            # Проверяем вхождение названия компании или её основного токена
            comp_matched = False
            if re.search(r"(?<!\w)" + re.escape(comp.lower()) + r"(?!\w)", low):
                comp_matched = True
            elif len(comp_tok) >= 4 and re.search(r"(?<!\w)" + re.escape(comp_tok) + r"(?!\w)", low):
                comp_matched = True

            if not comp_matched:
                continue

            # Определяем stage из самой строки или из текущей секции
            line_stage = None
            if any(w in low for w in ("interview", "screen", "hr-скрин", "hr скрин", "интервью", "скрининг", "приглаш", "созвон", "call")):
                line_stage = "interview"
            elif any(w in low for w in ("reject", "declin", "unfortunately", "not moving", "отказ", "отклон", "не подош", "других кандидат")):
                line_stage = "rejected_by_company"
            elif any(w in low for w in ("confirm", "received", "acknowledg", "thank you for applying", "подтвержд", "получен отклик", "заявка принята")):
                line_stage = "confirmed"
            else:
                line_stage = current_section_stage

            if not line_stage:
                continue

            # Извлекаем причину/комментарий после тире, двоеточия или вертикальной черты
            reason = None
            cleaned_line = re.sub(r"^[\-\*\d\.\|\s]+", "", line).strip("| ").strip()
            if "|" in cleaned_line:
                parts = [p.strip() for p in cleaned_line.split("|") if p.strip()]
                if len(parts) >= 3:
                    reason = parts[-1]
            if not reason:
                for sep in (" — ", " - ", ": ", " – "):
                    if sep in cleaned_line:
                        tail = cleaned_line.split(sep, 1)[1].strip()
                        if tail and tail.lower() != comp.lower():
                            reason = tail
                            break

            url_match = re.search(r"https?://[^\s\)\]\>\"']+", line)
            found_url = url_match.group(0).rstrip(".,;|") if url_match else None

            raw_updates.append({
                "company": comp,
                "stage": line_stage,
                "reason": reason,
                "email_url": found_url,
            })

    matched = match_updates_to_applied_jobs(raw_updates, applied_jobs)
    return {
        "summary": f"Разобрано по тексту отчёта: найдено совпадений {len(matched)}",
        "updates": matched,
    }


def sync_tracker_with_llm(
    applied_jobs: list[dict[str, Any]],
    report_text: str | None = None,
    skill_name: str = "@job-application-tracker",
    model: str | None = None,
    timeout_sec: int = config.JOB_ENRICH_TIMEOUT_SEC,
) -> dict[str, Any]:
    """Синхронизирует статусы Applied-вакансий через LLM (`agy` CLI) или разбор отчёта @job-application-tracker."""
    if not applied_jobs:
        return {
            "summary": "В разделе Applied пока нет вакансий для сверки.",
            "updates": [],
            "used_llm": False,
        }

    prompt = build_llm_sync_prompt(
        applied_jobs=applied_jobs,
        report_text=report_text,
        skill_name=skill_name,
    )
    allow_skills = not bool(report_text and report_text.strip())

    try:
        raw = run_agy(
            prompt=prompt,
            model=model,
            timeout_sec=timeout_sec,
            allow_skills=allow_skills,
        )
        data = extract_json_object(raw)
        raw_updates = data.get("updates") if isinstance(data.get("updates"), list) else []
        matched = match_updates_to_applied_jobs(raw_updates, applied_jobs)
        # Если LLM вернула текст, но мало совпадений в JSON, а у нас есть report_text — дополним эвристикой
        if report_text and not matched:
            heur = parse_tracker_report_heuristic(report_text, applied_jobs)
            matched = heur["updates"]
        return {
            "summary": data.get("summary") or f"Обновлено статусов вакансий: {len(matched)}",
            "updates": matched,
            "used_llm": True,
        }
    except Exception as e:
        logger.warning("LLM tracker sync failed (%s), trying heuristic parser if report_text is provided", e)
        if report_text and report_text.strip():
            heur = parse_tracker_report_heuristic(report_text, applied_jobs)
            return {
                "summary": heur["summary"],
                "updates": heur["updates"],
                "used_llm": False,
                "fallback_reason": str(e),
            }
        raise LLMError(
            f"Не удалось получить данные напрямую через agy CLI ({e}). "
            "Скопируйте промпт для @job-application-tracker в веб-Gemini и вставьте полученный отчёт в поле ниже."
        ) from e
