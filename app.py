import json
import threading
import time
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from pydantic import BaseModel

from agy_enrich import DEFAULT_MODEL
from enrichment_schema import JobEnrichment
from main import (
    add_blacklisted_board,
    enrich_and_score_pending_jobs,
    extract_root_domain,
    fetch_and_filter_jobs,
    get_blacklist_data,
    get_candidate_settings,
    init_db,
    match_blacklisted_domain,
    normalize_company_key,
    remove_blacklisted_board,
    remove_company_ats_map,
    save_candidate_settings,
    update_job_enrichment_and_score,
)
from skill_scorer import score_vacancy_by_skill

app = FastAPI(title="Job Filter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def allow_private_network_middleware(request: Request, call_next):
    if request.method == "OPTIONS" and request.headers.get("access-control-request-private-network") == "true":
        resp = Response(status_code=204)
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "*"
        resp.headers["Access-Control-Allow-Private-Network"] = "true"
        return resp
    response = await call_next(request)
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response

# Трекинг последней открытой пользователем вакансии (для связки при двойном переходе LinkedIn -> ATS)
last_opened_job: dict[str, str | float | None] = {
    "job_id": None,
    "title": None,
    "company": None,
    "url": None,
    "opened_ts": None,
    "opened_at": None,
}

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


class CandidateProfileRequest(BaseModel):
    profile_text: str = ""
    cv_text: str = ""


class AddBlacklistRequest(BaseModel):
    domain_or_url: str | None = None
    company: str | None = None
    job_id: str | None = None
    reason: str = "Невозможно заполнить форму (в чёрном списке)"
    hide_job: bool = True
    use_last_opened: bool = False


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


@app.get("/api/candidate")
def read_candidate_profile():
    conn = init_db()
    data = get_candidate_settings(conn)
    conn.close()
    return data


@app.put("/api/candidate")
def update_candidate_profile(body: CandidateProfileRequest):
    conn = init_db()
    data = save_candidate_settings(conn, body.profile_text, body.cv_text)
    conn.close()
    return data


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


@app.post("/api/jobs/{job_id}/opened")
def record_job_opened(job_id: str):
    """Фиксирует, какую вакансию пользователь только что открыл в браузере (для связки после редиректа с LinkedIn)."""
    conn = init_db()
    row = conn.execute(
        "SELECT job_id, title, company, url, apply_url, ats_domain FROM processed_jobs WHERE job_id = ?",
        (job_id,),
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    last_opened_job["job_id"] = row["job_id"]
    last_opened_job["title"] = row["title"]
    last_opened_job["company"] = row["company"]
    last_opened_job["url"] = row["url"]
    last_opened_job["opened_ts"] = time.time()
    last_opened_job["opened_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    return {"status": "ok", "last_opened_job": last_opened_job}


@app.get("/api/jobs/last-opened")
def get_last_opened_job():
    return {"last_opened_job": last_opened_job}


@app.get("/api/blacklist")
def read_blacklist():
    conn = init_db()
    data = get_blacklist_data(conn)
    conn.close()
    data["last_opened_job"] = last_opened_job
    return data


@app.get("/api/blacklist/check")
def check_url_in_blacklist(
    url: str = Query("", description="Текущий URL вкладки"),
    frames: str = Query("", description="Через запятую URL всех iframe на странице"),
    auto_link: bool = Query(True, description="Автоматически привязать обнаруженный говносайт к последней открытой вакансии"),
):
    """
    Проверяет URL вкладки и всех её iframe по базе черного списка (cims.com, icims.com и т.д.).
    Если обнаружен говносайт, а пользователь недавно кликнул на вакансию в Job Filter —
    автоматически запоминает, что у этой компании и вакансии этот говносайт!
    """
    conn = init_db()
    all_urls = [u.strip() for u in ([url] + frames.split(",")) if u.strip()]

    matched_info = None
    hit_url = None
    for u in all_urls:
        m = match_blacklisted_domain(conn, u)
        if m:
            matched_info = m
            hit_url = u
            break

    linked_job = None
    opened_ts = last_opened_job.get("opened_ts")
    is_recent = isinstance(opened_ts, (int, float)) and (time.time() - opened_ts) < 1800  # 30 минут

    if matched_info and auto_link and is_recent and last_opened_job.get("job_id"):
        add_blacklisted_board(
            conn,
            domain_or_url=hit_url or matched_info["domain"],
            company=str(last_opened_job.get("company") or ""),
            job_id=str(last_opened_job.get("job_id") or ""),
            reason=matched_info["reason"],
            hide_job=False,
        )
        linked_job = dict(last_opened_job)

    boards = [
        r["domain"]
        for r in conn.execute("SELECT domain FROM blacklisted_boards").fetchall()
    ]
    conn.close()

    return {
        "is_blacklisted": matched_info is not None,
        "matched_domain": matched_info["domain"] if matched_info else None,
        "reason": matched_info["reason"] if matched_info else None,
        "hit_url": hit_url,
        "linked_job": linked_job,
        "last_opened_job": last_opened_job if is_recent else None,
        "all_blacklisted_domains": boards,
    }


@app.post("/api/blacklist")
def create_blacklist_entry(body: AddBlacklistRequest):
    conn = init_db()
    job_id = body.job_id
    company = body.company

    opened_ts = last_opened_job.get("opened_ts")
    is_recent = isinstance(opened_ts, (int, float)) and (time.time() - opened_ts) < 1800

    if body.use_last_opened and is_recent:
        if not job_id and last_opened_job.get("job_id"):
            job_id = str(last_opened_job["job_id"])
        if not company and last_opened_job.get("company"):
            company = str(last_opened_job["company"])

    res = add_blacklisted_board(
        conn,
        domain_or_url=body.domain_or_url,
        company=company,
        job_id=job_id,
        reason=body.reason,
        hide_job=body.hide_job,
    )
    data = get_blacklist_data(conn)
    conn.close()
    return {"added": res, **data}


@app.delete("/api/blacklist/domain/{domain:path}")
def delete_blacklisted_domain(domain: str):
    conn = init_db()
    remove_blacklisted_board(conn, domain)
    data = get_blacklist_data(conn)
    conn.close()
    return data


@app.delete("/api/blacklist/company/{company_key:path}")
def delete_company_ats_entry(company_key: str):
    conn = init_db()
    remove_company_ats_map(conn, company_key)
    data = get_blacklist_data(conn)
    conn.close()
    return data


@app.get("/api/jobs")
def list_jobs(
    tab: str = Query("actionable", description="actionable | top | good | pending | applied | rejected"),
):
    conn = init_db()
    rows = conn.execute("SELECT * FROM processed_jobs ORDER BY processed_at DESC").fetchall()
    bad_rows = conn.execute("SELECT domain, reason FROM blacklisted_boards").fetchall()
    comp_rows = conn.execute("SELECT company_key, ats_domain FROM company_ats_map").fetchall()
    conn.close()

    bad_map = {r["domain"].lower(): (r["reason"] or "В чёрном списке / форма не заполняется") for r in bad_rows}
    if "cims.com" in bad_map and "icims.com" not in bad_map:
        bad_map["icims.com"] = bad_map["cims.com"]
    elif "icims.com" in bad_map and "cims.com" not in bad_map:
        bad_map["cims.com"] = bad_map["icims.com"]

    comp_ats_map = {r["company_key"]: r["ats_domain"] for r in comp_rows}

    stats = {
        "total_in_db": len(rows),
        "top_match": 0,
        "good_match": 0,
        "pending_llm": 0,
        "applied": 0,
        "rejected": 0,
        "bad_boards_count": len(bad_rows),
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

        comp_key = normalize_company_key(d.get("company"))
        ats_dom = (
            d.get("ats_domain")
            or extract_root_domain(d.get("apply_url"))
            or comp_ats_map.get(comp_key)
        )
        d["ats_domain"] = ats_dom

        bad_reason = None
        if ats_dom:
            low_dom = ats_dom.lower()
            if low_dom in bad_map:
                bad_reason = bad_map[low_dom]
            else:
                for b_dom, b_rsn in bad_map.items():
                    if low_dom.endswith("." + b_dom):
                        bad_reason = b_rsn
                        break
        if not bad_reason and comp_key and f"company:{comp_key}" in bad_map:
            bad_reason = bad_map[f"company:{comp_key}"]
            if not d["ats_domain"]:
                d["ats_domain"] = f"company:{comp_key}"

        d["is_bad_board"] = bad_reason is not None
        d["bad_board_reason"] = bad_reason

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

    # Сортировка: сначала НЕ-говносайты, затем Clean Title, затем Score DESC, затем дата
    def sort_key(item: dict):
        not_bad_board = 0 if item.get("is_bad_board") else 1
        sd = item.get("score_details") or {}
        clean_title = 1 if sd.get("has_clean_title", True) else 0
        sc = item.get("score") if item.get("score") is not None else -1
        dt = item.get("date_posted") or ""
        return (not_bad_board, clean_title, sc, dt)

    items.sort(key=sort_key, reverse=True)
    return {"stats": stats, "jobs": items, "last_opened_job": last_opened_job}


UI_HTML_PATH = Path(__file__).parent / "ui.html"


@app.get("/", response_class=HTMLResponse)
def index():
    if UI_HTML_PATH.is_file():
        return UI_HTML_PATH.read_text(encoding="utf-8")
    return "<h1>UI file not found</h1>"

