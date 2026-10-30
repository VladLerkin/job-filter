"""Сервис обработки резюме: извлечение текста из PDF, вычисление diff навыков и применение изменений."""
import io
import json
import logging
import re
import sqlite3
from pypdf import PdfReader

from job_filter.models.cv import ParsedCVResult, ParsedSkillItem
from job_filter.repositories import candidate_repo, skills_repo
from job_filter.scoring.matrix import invalidate_matrix_cache

logger = logging.getLogger(__name__)


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Извлекает и нормализует текстовый слой из переданного PDF файла."""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except Exception as e:
        raise ValueError(f"Не удалось открыть PDF файл: {e}")

    pages_text = []
    for idx, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
            if text.strip():
                pages_text.append(text.strip())
        except Exception:
            continue

    combined = "\n\n".join(pages_text)
    combined = re.sub(r"(\w+)-\n(\w+)", r"\1\2", combined)
    combined = re.sub(r"[ \t]+", " ", combined)

    if len(combined.strip()) < 50:
        raise ValueError(
            "В PDF-файле не обнаружен текстовый слой (возможно, это отсканированный документ или изображение). "
            "Пожалуйста, загрузите PDF с текстовым слоем или скопируйте текст вручную."
        )
    return combined.strip()


def compute_skills_diff(
    extracted_skills: list[ParsedSkillItem],
    existing_skills: list[dict],
    categories: list[dict],
) -> list[dict]:
    """
    Сравнивает извлеченные ИИ навыки с существующими в базе данными candidate_skills.
    Возвращает структурированный diff для модального окна подтверждения в UI.
    """
    cat_map = {c["category_id"]: c for c in categories}
    default_cat_id = categories[0]["category_id"] if categories else "core_backend"

    exist_map = {s["skill_id"]: s for s in existing_skills}
    seen_skill_ids = set()

    diff_list = []

    for es in extracted_skills:
        sid = es.skill_id.strip().lower()
        if not sid:
            continue
        seen_skill_ids.add(sid)

        cid = es.category_id.strip().lower()
        if cid not in cat_map:
            cid = default_cat_id
        cat = cat_map.get(cid, {})
        mult = float(cat.get("multiplier", 2.0))
        max_p = int(cat.get("max_points", 20))

        # Вычисляем предварительные баллы скоринга
        if mult < 0:
            new_points = max_p
        else:
            new_points = min(round(es.years_experience * mult), max_p)

        if sid in exist_map:
            existing = exist_map[sid]
            old_years = float(existing.get("years_experience", 0.0))
            old_points = int(existing.get("weight_points", 0))
            is_changed = (abs(old_years - es.years_experience) >= 0.25) or (old_points != new_points)

            diff_list.append({
                "skill_id": sid,
                "name": es.name,
                "category_id": cid,
                "category_title": cat.get("title", cid),
                "status": "updated" if is_changed else "unchanged",
                "selected": is_changed,
                "old_years": old_years,
                "new_years": es.years_experience,
                "old_points": old_points,
                "new_points": new_points,
                "is_primary": es.is_primary,
                "aliases": es.aliases or [sid],
            })
        else:
            diff_list.append({
                "skill_id": sid,
                "name": es.name,
                "category_id": cid,
                "category_title": cat.get("title", cid),
                "status": "new",
                "selected": True,
                "old_years": 0.0,
                "new_years": es.years_experience,
                "old_points": 0,
                "new_points": new_points,
                "is_primary": es.is_primary,
                "aliases": es.aliases or [sid],
            })

    status_order = {"new": 0, "updated": 1, "unchanged": 2}
    diff_list.sort(key=lambda x: (status_order.get(x["status"], 9), -x["new_points"], x["name"]))

    return diff_list


def apply_cv_analysis(
    conn: sqlite3.Connection,
    update_cv_text: bool,
    structured_cv: str,
    update_profile_text: bool,
    candidate_summary: str,
    apply_skills: bool,
    skills_to_apply: list[dict],
) -> tuple[int, bool]:
    """
    Применяет подтверждённые изменения из CV в базу candidate_settings и candidate_skills.
    Возвращает (skills_applied_count, cv_updated).
    """
    cv_updated = False
    if update_cv_text and structured_cv:
        current = candidate_repo.get_settings(conn)
        profile_text = current.get("profile_text", "")
        if update_profile_text and candidate_summary:
            if profile_text:
                profile_text = f"{candidate_summary}\n\n{profile_text}"
            else:
                profile_text = candidate_summary
        candidate_repo.save_settings(conn, profile_text=profile_text, cv_text=structured_cv)
        cv_updated = True

    skills_applied = 0
    if apply_skills and skills_to_apply:
        for s in skills_to_apply:
            sid = s.get("skill_id", "").strip().lower()
            cid = s.get("category_id", "").strip().lower()
            name = s.get("name", "").strip()
            years = float(s.get("years_experience", 0.0))
            pts = int(s.get("weight_points", 0)) if s.get("weight_points") is not None else None
            is_prim = bool(s.get("is_primary", False))
            aliases = s.get("aliases", [])
            if sid and name and cid:
                if not skills_repo.get_category(conn, cid):
                    skills_repo.upsert_category(conn, cid, cid.replace("_", " ").title(), 2.0, 20, 99)
                if pts is None:
                    cat = skills_repo.get_category(conn, cid)
                    if cat:
                        m = float(cat["multiplier"])
                        max_p = int(cat["max_points"])
                        pts = max_p if m < 0 else min(round(years * m), max_p)
                    else:
                        pts = int(years * 2)

                aliases_list = [a.strip().lower() for a in aliases if a and a.strip()]
                if name.lower() not in aliases_list:
                    aliases_list.append(name.lower())

                skills_repo.upsert_skill(
                    conn,
                    skill_id=sid,
                    category_id=cid,
                    name=name,
                    years_experience=years,
                    weight_points=pts,
                    is_primary=is_prim,
                    aliases=aliases_list,
                )
                skills_applied += 1
        invalidate_matrix_cache()

    return skills_applied, cv_updated
