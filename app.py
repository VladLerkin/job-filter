import json
import threading
import time
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

from agy_enrich import DEFAULT_MODEL
from enrichment_schema import JobEnrichment
from main import (
    enrich_and_score_pending_jobs,
    fetch_and_filter_jobs,
    init_db,
    update_job_enrichment_and_score,
)
from skill_scorer import score_vacancy_by_skill

app = FastAPI(title="LinkedIn AI Vacancy Filter & Enricher")

# Глобальное состояние фонового пайплайна для стриминга логов в браузер
pipeline_lock = threading.Lock()
pipeline_state = {
    "running": False,
    "logs": [],
    "started_at": None,
    "finished_at": None,
}


class RunPipelineRequest(BaseModel):
    search_terms: list[str] = [
        "Agentic Engineer Remote",
        "AI Agent Engineer Remote",
        "Software Engineer Remote",
    ]
    site_names: list[str] = ["linkedin"]
    location: str = "EMEA"
    country_indeed: str = "uk"
    results_wanted: int = 20
    hours_old: int = 4
    easy_apply: bool = False
    llm_model: str = DEFAULT_MODEL
    llm_limit: int = 15
    enrich_only: bool = False


class UpdateStatusRequest(BaseModel):
    user_status: Literal["new", "applied", "saved", "hidden"]


def _append_log(msg: str) -> None:
    ts = time.strftime("%H:%M:%S")
    pipeline_state["logs"].append(f"[{ts}] {msg}")


def _worker_run(req: RunPipelineRequest) -> None:
    try:
        if req.enrich_only:
            conn = init_db()
            enrich_and_score_pending_jobs(
                conn,
                model=req.llm_model,
                limit=req.llm_limit,
                on_progress=_append_log,
            )
            conn.close()
        else:
            fetch_and_filter_jobs(
                search_terms=req.search_terms,
                site_names=req.site_names,
                location=req.location,
                country_indeed=req.country_indeed,
                results_wanted=req.results_wanted,
                hours_old=req.hours_old,
                easy_apply=True if req.easy_apply else None,
                run_llm_enrichment=True,
                llm_model=req.llm_model,
                llm_limit=req.llm_limit,
                on_progress=_append_log,
            )
        _append_log("✅ Пайплайн успешно завершен!")
    except Exception as e:
        _append_log(f"❌ Ошибка выполнения пайплайна: {e}")
    finally:
        pipeline_state["running"] = False
        pipeline_state["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")


@app.post("/api/pipeline/start")
def start_pipeline(req: RunPipelineRequest):
    with pipeline_lock:
        if pipeline_state["running"]:
            return {"status": "already_running", "logs_count": len(pipeline_state["logs"])}
        pipeline_state["running"] = True
        pipeline_state["logs"] = []
        pipeline_state["started_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        pipeline_state["finished_at"] = None

        t = threading.Thread(target=_worker_run, args=(req,), daemon=True)
        t.start()
        return {"status": "started"}


@app.get("/api/pipeline/status")
def get_pipeline_status(since: int = 0):
    logs = pipeline_state["logs"]
    return {
        "running": pipeline_state["running"],
        "started_at": pipeline_state["started_at"],
        "finished_at": pipeline_state["finished_at"],
        "logs": logs[since:],
        "next_index": len(logs),
    }


@app.post("/api/jobs/rescore")
def rescore_all_enriched_jobs():
    """Пересчитывает баллы по скиллу для всех уже обогащенных через LLM вакансий без повторного вызова LLM."""
    conn = init_db()
    rows = conn.execute(
        """
        SELECT job_id, title, company, date_posted, seniority_level, industry, salary, description, enrichment_json
        FROM processed_jobs
        WHERE enrichment_json IS NOT NULL
        """
    ).fetchall()
    updated = 0
    for r in rows:
        try:
            enrichment = JobEnrichment.model_validate_json(r["enrichment_json"])
            score_res = score_vacancy_by_skill(
                title=r["title"] or "",
                company=r["company"],
                date_posted=r["date_posted"],
                seniority_level=r["seniority_level"],
                industry=r["industry"],
                salary_text=r["salary"],
                description=r["description"] or "",
                enrichment=enrichment,
            )
            update_job_enrichment_and_score(conn, r["job_id"], enrichment, score_res)
            updated += 1
        except Exception:
            continue
    conn.close()
    return {"rescored": updated}


@app.patch("/api/jobs/{job_id}/status")
def update_job_status(job_id: str, body: UpdateStatusRequest):
    conn = init_db()
    cur = conn.execute(
        "UPDATE processed_jobs SET user_status = ? WHERE job_id = ?",
        (body.user_status, job_id),
    )
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, "user_status": body.user_status}


@app.get("/api/jobs")
def list_jobs(
    tab: str = Query("actionable", description="actionable | top | good | pending | applied | rejected"),
):
    conn = init_db()
    rows = conn.execute("SELECT * FROM processed_jobs ORDER BY processed_at DESC").fetchall()
    conn.close()

    stats = {
        "total_in_db": len(rows),
        "top_match": 0,
        "good_match": 0,
        "pending_llm": 0,
        "applied": 0,
        "rejected": 0,
    }

    items = []
    for r in rows:
        d = dict(r)
        enrichment = None
        score_details = None
        if d.get("enrichment_json"):
            try:
                enrichment = json.loads(d["enrichment_json"])
            except Exception:
                enrichment = None
        if d.get("score_details_json"):
            try:
                score_details = json.loads(d["score_details_json"])
            except Exception:
                score_details = None

        d["enrichment"] = enrichment
        d["score_details"] = score_details
        d.pop("enrichment_json", None)
        d.pop("score_details_json", None)

        u_status = d.get("user_status") or "new"
        score = d.get("score")
        has_desc = bool(d.get("description"))
        reject_reason = d.get("reject_reason")

        # Подсчет статистики
        if u_status == "applied":
            stats["applied"] += 1
        elif u_status == "hidden":
            stats["rejected"] += 1
        elif score is not None:
            if d.get("matched") == 1 and score >= 70:
                stats["top_match"] += 1
            elif d.get("matched") == 1 and 50 <= score < 70:
                stats["good_match"] += 1
            else:
                stats["rejected"] += 1
        elif has_desc and not reject_reason:
            stats["pending_llm"] += 1
        else:
            stats["rejected"] += 1

        # Фильтрация по выбранной вкладке
        if tab == "applied":
            if u_status == "applied":
                items.append(d)
        elif tab == "pending":
            if score is None and has_desc and not reject_reason and u_status != "hidden":
                items.append(d)
        elif tab == "rejected":
            if u_status == "hidden" or (score is not None and (score < 50 or d.get("matched") == 0)) or reject_reason:
                items.append(d)
        elif tab == "top":
            if u_status not in ("applied", "hidden") and d.get("matched") == 1 and score is not None and score >= 70:
                items.append(d)
        elif tab == "good":
            if u_status not in ("applied", "hidden") and d.get("matched") == 1 and score is not None and 50 <= score < 70:
                items.append(d)
        else:  # actionable (top + good)
            if u_status not in ("applied", "hidden") and d.get("matched") == 1 and score is not None and score >= 50:
                items.append(d)

    # Сортировка по правилам скилла: сначала Clean Title (без чужих технологий в заголовке), затем Score DESC, затем дата
    def sort_key(item: dict):
        sd = item.get("score_details") or {}
        clean_title = 1 if sd.get("has_clean_title", True) else 0
        sc = item.get("score") if item.get("score") is not None else -1
        dt = item.get("date_posted") or ""
        return (clean_title, sc, dt)

    items.sort(key=sort_key, reverse=True)
    return {"stats": stats, "jobs": items}


UI_HTML_PATH = Path(__file__).parent / "ui.html"


@app.get("/", response_class=HTMLResponse)
def index():
    if UI_HTML_PATH.is_file():
        return UI_HTML_PATH.read_text(encoding="utf-8")
    return "<h1>UI file not found</h1>"

