from collections.abc import Callable
from datetime import datetime, timezone
import json
from pathlib import Path
import random
import re
import sqlite3
import time
from urllib.parse import parse_qs, unquote, urlparse

from bs4 import BeautifulSoup
from jobspy import scrape_jobs
from jobspy.linkedin.constant import headers as linkedin_headers
from jobspy.linkedin.util import criteria
from markdownify import markdownify as md
import pandas as pd
import requests

from agy_enrich import DEFAULT_MODEL, enrich_job_with_agy
from enrichment_schema import JobEnrichment
from skill_scorer import SkillScoreResult, score_vacancy_by_skill

DB_PATH = Path(__file__).parent / "jobs.db"


def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Инициализирует SQLite базу и выполняет мягкую миграцию новых колонок."""
    conn = sqlite3.connect(db_path, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS processed_jobs (
            job_id TEXT PRIMARY KEY,
            site TEXT DEFAULT 'linkedin',
            title TEXT,
            company TEXT,
            url TEXT,
            date_posted TEXT,
            seniority_level TEXT,
            employment_type TEXT,
            job_function TEXT,
            industry TEXT,
            salary TEXT,
            description TEXT,
            matched INTEGER,
            reject_reason TEXT,
            processed_at TEXT,
            enrichment_json TEXT,
            score INTEGER,
            tier TEXT,
            score_details_json TEXT,
            user_status TEXT DEFAULT 'new'
        )
        """
    )

    existing_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(processed_jobs)").fetchall()
    }
    new_cols = {
        "site": "TEXT DEFAULT 'linkedin'",
        "location": "TEXT",
        "is_remote": "INTEGER",
        "seniority_level": "TEXT",
        "employment_type": "TEXT",
        "job_function": "TEXT",
        "industry": "TEXT",
        "salary": "TEXT",
        "description": "TEXT",
        "reject_reason": "TEXT",
        "enrichment_json": "TEXT",
        "score": "INTEGER",
        "tier": "TEXT",
        "score_details_json": "TEXT",
        "user_status": "TEXT DEFAULT 'new'",
        "apply_url": "TEXT",
        "ats_domain": "TEXT",
    }
    for col_name, col_type in new_cols.items():
        if col_name not in existing_cols:
            conn.execute(f"ALTER TABLE processed_jobs ADD COLUMN {col_name} {col_type}")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS blacklisted_boards (
            domain TEXT PRIMARY KEY,
            reason TEXT,
            created_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS company_ats_map (
            company_key TEXT PRIMARY KEY,
            company_name TEXT,
            ats_domain TEXT,
            sample_url TEXT,
            updated_at TEXT
        )
        """
    )

    now_iso = datetime.now(timezone.utc).isoformat()
    default_bad_domains = [
        ("cims.com", "iCIMS (cims.com) — невозможно нормально заполнить форму"),
        ("icims.com", "iCIMS (icims.com) — невозможно нормально заполнить форму"),
    ]
    for dom, rsn in default_bad_domains:
        conn.execute(
            """
            INSERT OR IGNORE INTO blacklisted_boards (domain, reason, created_at)
            VALUES (?, ?, ?)
            """,
            (dom, rsn, now_iso),
        )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS candidate_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            profile_text TEXT,
            cv_text TEXT,
            updated_at TEXT
        )
        """
    )
    row = conn.execute("SELECT id FROM candidate_settings WHERE id = 1").fetchone()
    if not row:
        conn.execute(
            """
            INSERT INTO candidate_settings (id, profile_text, cv_text, updated_at)
            VALUES (1, '', '', ?)
            """,
            (datetime.now(timezone.utc).isoformat(),),
        )

    # Таблицы категорий и матрицы навыков для гибкого скоринга
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS skill_categories (
            category_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            multiplier REAL DEFAULT 2.0,
            max_points INTEGER DEFAULT 30,
            sort_order INTEGER DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS candidate_skills (
            skill_id TEXT PRIMARY KEY,
            category_id TEXT NOT NULL,
            name TEXT NOT NULL,
            years_experience REAL DEFAULT 0.0,
            weight_points INTEGER DEFAULT 0,
            is_primary INTEGER DEFAULT 0,
            aliases_json TEXT,
            FOREIGN KEY (category_id) REFERENCES skill_categories(category_id)
        )
        """
    )

    # Инициализируем стартовые категории и навыки, если таблицы пустые
    cat_count = conn.execute("SELECT COUNT(*) FROM skill_categories").fetchone()[0]
    if cat_count == 0:
        default_categories = [
            ("ai_agentic", "🤖 AI & Agentic Systems", 15.0, 30, 1),
            ("core_backend", "☕ Core Backend & Languages", 2.0, 20, 2),
            ("secondary_backend", "🐍 Secondary Languages / TS", 3.0, 18, 3),
            ("arch_infra", "🏗️ Architecture & Cloud / DevOps", 2.0, 15, 4),
            ("domains", "💼 Business Domains (FinTech / Banking)", 2.0, 10, 5),
            ("alien", "🚫 Чужой стек (Штрафы)", -1.0, -20, 6),
            ("legacy", "🦖 Устаревший стек (Штрафы)", -1.0, -30, 7),
        ]
        conn.executemany(
            "INSERT INTO skill_categories (category_id, title, multiplier, max_points, sort_order) VALUES (?, ?, ?, ?, ?)",
            default_categories,
        )

        default_skills = [
            # AI & Agentic
            ("langgraph", "ai_agentic", "LangGraph", 2.0, 30, 1, '["langgraph", "langchain", "crewai", "koog"]'),
            ("agentic", "ai_agentic", "AI Agents / Multi-Agent", 2.0, 30, 1, '["agentic", "agentic ai", "ai agentic", "ai agents", "agents", "multi-agent", "multi agent", "a2a"]'),
            ("rag", "ai_agentic", "RAG & Vector DB", 2.0, 20, 1, '["rag", "embeddings", "vector db", "mem0", "memsearch"]'),
            ("mcp", "ai_agentic", "MCP Protocol", 1.5, 20, 1, '["mcp", "model context protocol"]'),
            ("llm", "ai_agentic", "LLMs / GenAI / Prompt Engineering", 2.5, 25, 1, '["llm", "llms", "genai", "generative ai", "prompt engineering", "claude", "openai", "anthropic", "gpt"]'),
            ("langsmith", "ai_agentic", "LLM Observability", 1.5, 15, 0, '["langsmith", "langfuse", "hivetrace"]'),
            # Core Backend
            ("java", "core_backend", "Java", 10.0, 20, 1, '["java", "jvm"]'),
            ("kotlin", "core_backend", "Kotlin", 5.0, 20, 1, '["kotlin", "kmp", "kotlin multiplatform"]'),
            ("spring_boot", "core_backend", "Spring Boot", 8.0, 20, 1, '["spring", "spring boot", "spring data", "spring security", "spring ai"]'),
            ("ktor", "core_backend", "Ktor", 3.0, 15, 0, '["ktor"]'),
            # Secondary Backend
            ("python", "secondary_backend", "Python", 4.0, 18, 1, '["python"]'),
            ("typescript", "secondary_backend", "TypeScript / Node.js", 2.0, 9, 0, '["typescript", "ts", "node", "nodejs", "node.js"]'),
            # Architecture & Cloud
            ("microservices", "arch_infra", "Microservices & Distributed Systems", 8.0, 15, 1, '["microservices", "distributed systems", "high-load", "high load", "system design"]'),
            ("kafka", "arch_infra", "Kafka & Event-Driven", 6.0, 15, 1, '["kafka", "event-driven", "event driven", "event driven architecture", "rabbitmq"]'),
            ("postgresql", "arch_infra", "PostgreSQL / SQL", 8.0, 15, 1, '["postgresql", "postgres", "sql", "oracle", "mssql"]'),
            ("docker_k8s", "arch_infra", "Docker & Kubernetes", 6.0, 15, 1, '["docker", "kubernetes", "k8s"]'),
            ("aws_cloud", "arch_infra", "AWS / Cloud Native", 5.0, 15, 1, '["aws", "google cloud", "gcp", "cloud architecture", "cloud native"]'),
            ("rest_api", "arch_infra", "REST & OpenAPI", 8.0, 12, 0, '["rest", "rest api", "restful", "openapi", "swagger"]'),
            # Business Domains
            ("fintech", "domains", "FinTech & Banking / Payments", 5.0, 10, 1, '["fintech", "banking", "payments", "billing", "brokerage", "custody", "trading"]'),
            ("enterprise", "domains", "Enterprise Systems (ECM/CRM/ERP)", 4.0, 8, 0, '["enterprise", "ecm", "crm", "bpm", "erp"]'),
            # Alien stack
            ("go", "alien", "Golang / Go", 0.0, -20, 0, '["go", "golang"]'),
            ("csharp", "alien", "C# / .NET", 0.0, -20, 0, '["c#", ".net"]'),
            ("cpp", "alien", "C++", 0.0, -20, 0, '["c++"]'),
            ("rust", "alien", "Rust", 0.0, -20, 0, '["rust"]'),
            ("php", "alien", "PHP", 0.0, -20, 0, '["php", "wordpress", "drupal", "laravel", "symfony"]'),
            ("ruby", "alien", "Ruby / Rails", 0.0, -20, 0, '["ruby", "rails"]'),
            # Legacy
            ("one_c", "legacy", "1C", 0.0, -30, 0, '["1c", "1с", "oscript"]'),
            ("sap", "legacy", "SAP / ABAP", 0.0, -30, 0, '["sap", "abap"]'),
            ("salesforce", "legacy", "Salesforce", 0.0, -30, 0, '["salesforce", "apex"]'),
        ]
        conn.executemany(
            "INSERT INTO candidate_skills (skill_id, category_id, name, years_experience, weight_points, is_primary, aliases_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
            default_skills,
        )

    conn.commit()
    return conn


def get_candidate_settings(conn: sqlite3.Connection) -> dict[str, str]:
    row = conn.execute(
        "SELECT profile_text, cv_text, updated_at FROM candidate_settings WHERE id = 1"
    ).fetchone()
    if not row:
        return {"profile_text": "", "cv_text": "", "updated_at": ""}
    return {
        "profile_text": row["profile_text"] or "",
        "cv_text": row["cv_text"] or "",
        "updated_at": row["updated_at"] or "",
    }


def get_skill_matrix_data(conn: sqlite3.Connection) -> dict:
    categories = [
        dict(r)
        for r in conn.execute(
            "SELECT category_id, title, multiplier, max_points, sort_order FROM skill_categories ORDER BY sort_order ASC, category_id ASC"
        ).fetchall()
    ]
    skills = [
        dict(r)
        for r in conn.execute(
            "SELECT skill_id, category_id, name, years_experience, weight_points, is_primary, aliases_json FROM candidate_skills ORDER BY years_experience DESC, name ASC"
        ).fetchall()
    ]
    for s in skills:
        if s.get("aliases_json"):
            try:
                s["aliases"] = json.loads(s["aliases_json"])
            except Exception:
                s["aliases"] = []
        else:
            s["aliases"] = []
    return {"categories": categories, "skills": skills}


def save_skill_category(
    conn: sqlite3.Connection,
    category_id: str,
    title: str,
    multiplier: float = 2.0,
    max_points: int = 30,
    sort_order: int = 0,
) -> dict:
    cid = category_id.strip().lower()
    conn.execute(
        """
        INSERT INTO skill_categories (category_id, title, multiplier, max_points, sort_order)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(category_id) DO UPDATE SET
            title = excluded.title,
            multiplier = excluded.multiplier,
            max_points = excluded.max_points,
            sort_order = excluded.sort_order
        """,
        (cid, title.strip(), multiplier, max_points, sort_order),
    )
    conn.commit()
    return {"category_id": cid, "title": title, "multiplier": multiplier, "max_points": max_points, "sort_order": sort_order}


def delete_skill_category(conn: sqlite3.Connection, category_id: str) -> None:
    cid = category_id.strip().lower()
    # Удаляем или перемещаем связанные навыки
    conn.execute("DELETE FROM candidate_skills WHERE category_id = ?", (cid,))
    conn.execute("DELETE FROM skill_categories WHERE category_id = ?", (cid,))
    conn.commit()


def save_candidate_skill(
    conn: sqlite3.Connection,
    skill_id: str,
    category_id: str,
    name: str,
    years_experience: float = 0.0,
    weight_points: int | None = None,
    is_primary: bool = False,
    aliases: list[str] | None = None,
) -> dict:
    sid = skill_id.strip().lower()
    cid = category_id.strip().lower()
    name_clean = name.strip()

    # Если weight_points не задан вручную, рассчитываем по множителю категории
    if weight_points is None:
        cat = conn.execute("SELECT multiplier, max_points FROM skill_categories WHERE category_id = ?", (cid,)).fetchone()
        if cat:
            mult = float(cat["multiplier"])
            max_p = int(cat["max_points"])
            if mult < 0:
                calc = max_p
            else:
                calc = round(years_experience * mult)
                calc = min(calc, max_p)
            weight_points = int(calc)
        else:
            weight_points = int(years_experience * 2)

    aliases_list = [a.strip().lower() for a in (aliases or []) if a.strip()]
    if name_clean.lower() not in aliases_list:
        aliases_list.append(name_clean.lower())
    aliases_json = json.dumps(aliases_list, ensure_ascii=False)

    conn.execute(
        """
        INSERT INTO candidate_skills (skill_id, category_id, name, years_experience, weight_points, is_primary, aliases_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(skill_id) DO UPDATE SET
            category_id = excluded.category_id,
            name = excluded.name,
            years_experience = excluded.years_experience,
            weight_points = excluded.weight_points,
            is_primary = excluded.is_primary,
            aliases_json = excluded.aliases_json
        """,
        (sid, cid, name_clean, years_experience, weight_points, 1 if is_primary else 0, aliases_json),
    )
    conn.commit()
    return {
        "skill_id": sid,
        "category_id": cid,
        "name": name_clean,
        "years_experience": years_experience,
        "weight_points": weight_points,
        "is_primary": is_primary,
        "aliases": aliases_list,
    }


def delete_candidate_skill(conn: sqlite3.Connection, skill_id: str) -> None:
    sid = skill_id.strip().lower()
    conn.execute("DELETE FROM candidate_skills WHERE skill_id = ?", (sid,))
    conn.commit()


def save_candidate_settings(
    conn: sqlite3.Connection,
    profile_text: str,
    cv_text: str,
) -> dict[str, str]:
    now_iso = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO candidate_settings (id, profile_text, cv_text, updated_at)
        VALUES (1, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            profile_text = excluded.profile_text,
            cv_text = excluded.cv_text,
            updated_at = excluded.updated_at
        """,
        (profile_text, cv_text, now_iso),
    )
    conn.commit()
    return {"profile_text": profile_text, "cv_text": cv_text, "updated_at": now_iso}


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


def match_blacklisted_domain(
    conn: sqlite3.Connection,
    url_or_domain: str | None,
) -> dict[str, str] | None:
    """Проверяет, входит ли URL или домен в черный список говносайтов."""
    if not url_or_domain:
        return None
    raw = url_or_domain.strip()
    if not raw:
        return None
    host = raw.lower()
    if "://" in raw or "/" in raw:
        try:
            host = (urlparse(raw if "://" in raw else "https://" + raw).hostname or "").lower().strip(".")
        except Exception:
            pass
    if host.startswith("www."):
        host = host[4:]
    root = extract_root_domain(host) or host

    rows = conn.execute("SELECT domain, reason FROM blacklisted_boards").fetchall()
    bad_map = {r["domain"].lower(): (r["reason"] or "В черном списке") for r in rows}

    # Эквивалентность cims.com <-> icims.com
    candidates_to_check = [host, root]
    if root in ("cims.com", "icims.com") or host.endswith(".cims.com") or host.endswith(".icims.com"):
        candidates_to_check.extend(["cims.com", "icims.com"])

    for cand in candidates_to_check:
        if cand in bad_map:
            return {"domain": cand, "reason": bad_map[cand]}
    for bad_dom, rsn in bad_map.items():
        if host == bad_dom or host.endswith("." + bad_dom):
            return {"domain": bad_dom, "reason": rsn}
    return None


def get_company_ats_info(conn: sqlite3.Connection, company: str | None) -> dict[str, str] | None:
    key = normalize_company_key(company)
    if not key:
        return None
    row = conn.execute(
        "SELECT company_name, ats_domain, sample_url, updated_at FROM company_ats_map WHERE company_key = ?",
        (key,),
    ).fetchone()
    if not row:
        return None
    return dict(row)


def get_blacklist_data(conn: sqlite3.Connection) -> dict:
    boards = [
        dict(r)
        for r in conn.execute(
            "SELECT domain, reason, created_at FROM blacklisted_boards ORDER BY created_at DESC"
        ).fetchall()
    ]
    companies = [
        dict(r)
        for r in conn.execute(
            "SELECT company_key, company_name, ats_domain, sample_url, updated_at FROM company_ats_map ORDER BY updated_at DESC"
        ).fetchall()
    ]
    return {"boards": boards, "companies": companies}


def add_blacklisted_board(
    conn: sqlite3.Connection,
    domain_or_url: str | None = None,
    company: str | None = None,
    job_id: str | None = None,
    reason: str = "Невозможно заполнить форму (в чёрном списке)",
    hide_job: bool = True,
) -> dict:
    """
    Добавляет домен в черный список, привязывает его к компании (если известна)
    и обновляет все вакансии этой компании / с этим доменом в БД.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    domain = extract_root_domain(domain_or_url) if domain_or_url else None

    if job_id and not company:
        row = conn.execute("SELECT company, apply_url, ats_domain FROM processed_jobs WHERE job_id = ?", (job_id,)).fetchone()
        if row:
            company = row["company"]
            if not domain:
                domain = row["ats_domain"] or extract_root_domain(row["apply_url"])

    if not domain and company:
        # Если пользователь не знает точный домен, но банит компанию как ведущую на говносайт
        domain = f"company:{normalize_company_key(company)}"

    if domain:
        conn.execute(
            """
            INSERT INTO blacklisted_boards (domain, reason, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(domain) DO UPDATE SET
                reason = excluded.reason
            """,
            (domain, reason, now_iso),
        )
        # Если банится cims.com — синхронно баним и icims.com
        if domain == "cims.com":
            conn.execute(
                "INSERT OR IGNORE INTO blacklisted_boards (domain, reason, created_at) VALUES (?, ?, ?)",
                ("icims.com", reason, now_iso),
            )
        elif domain == "icims.com":
            conn.execute(
                "INSERT OR IGNORE INTO blacklisted_boards (domain, reason, created_at) VALUES (?, ?, ?)",
                ("cims.com", reason, now_iso),
            )

    comp_key = normalize_company_key(company)
    if comp_key and domain:
        conn.execute(
            """
            INSERT INTO company_ats_map (company_key, company_name, ats_domain, sample_url, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(company_key) DO UPDATE SET
                ats_domain = excluded.ats_domain,
                sample_url = COALESCE(excluded.sample_url, company_ats_map.sample_url),
                updated_at = excluded.updated_at
            """,
            (comp_key, (company or "").strip(), domain, domain_or_url, now_iso),
        )
        conn.execute(
            """
            UPDATE processed_jobs
            SET ats_domain = COALESCE(ats_domain, ?),
                apply_url = COALESCE(apply_url, ?)
            WHERE lower(trim(company)) = ?
            """,
            (domain, domain_or_url if (domain_or_url and "://" in domain_or_url) else None, comp_key),
        )

    if job_id:
        if hide_job:
            conn.execute(
                """
                UPDATE processed_jobs
                SET user_status = 'hidden',
                    ats_domain = COALESCE(?, ats_domain),
                    apply_url = COALESCE(?, apply_url),
                    reject_reason = COALESCE(reject_reason, ?)
                WHERE job_id = ?
                """,
                (
                    domain,
                    domain_or_url if (domain_or_url and "://" in domain_or_url) else None,
                    f"bad_board:{domain or 'unknown'}",
                    job_id,
                ),
            )
        else:
            conn.execute(
                """
                UPDATE processed_jobs
                SET ats_domain = COALESCE(?, ats_domain),
                    apply_url = COALESCE(?, apply_url)
                WHERE job_id = ?
                """,
                (
                    domain,
                    domain_or_url if (domain_or_url and "://" in domain_or_url) else None,
                    job_id,
                ),
            )

    conn.commit()
    return {
        "domain": domain,
        "company": company,
        "job_id": job_id,
        "reason": reason,
    }


def remove_blacklisted_board(conn: sqlite3.Connection, domain: str) -> None:
    d = (domain or "").strip().lower()
    conn.execute("DELETE FROM blacklisted_boards WHERE lower(domain) = ?", (d,))
    conn.commit()


def remove_company_ats_map(conn: sqlite3.Connection, company_key: str) -> None:
    k = normalize_company_key(company_key)
    conn.execute("DELETE FROM company_ats_map WHERE company_key = ?", (k,))
    conn.commit()


def extract_linkedin_apply_url(soup: BeautifulSoup) -> str | None:
    """
    Пытается извлечь прямую внешнюю ссылку (applyUrl) из гостевой HTML-карточки LinkedIn,
    если вакансия ведет на внешний ATS (не Easy Apply).
    """
    candidates: list[str] = []

    code_tag = soup.find("code", id="applyUrl")
    if code_tag:
        raw_html = str(code_tag)
        m = re.search(r"<!--\s*\"?(https?://[^\s\"<>]+)\"?\s*-->", raw_html)
        if m:
            candidates.append(m.group(1))
        elif code_tag.get_text(strip=True):
            candidates.append(code_tag.get_text(strip=True).strip('"'))

    for a_tag in soup.find_all("a", href=True):
        cls = " ".join(a_tag.get("class") or [])
        trk = str(a_tag.get("data-tracking-control-name") or "")
        href = str(a_tag["href"])
        if "apply" in cls.lower() or "apply" in trk.lower() or "externalApply" in href:
            candidates.append(href)

    for raw_url in candidates:
        try:
            parsed = urlparse(raw_url)
            qs = parse_qs(parsed.query)
            if "url" in qs and qs["url"]:
                ext = unquote(qs["url"][0]).strip()
                ext_host = (urlparse(ext).hostname or "").lower()
                if ext_host and "linkedin.com" not in ext_host:
                    return ext
            host = (parsed.hostname or "").lower()
            if host and "linkedin.com" not in host:
                return raw_url
        except Exception:
            continue

    return None


def get_processed_ids(conn: sqlite3.Connection) -> set[str]:
    cursor = conn.execute("SELECT job_id FROM processed_jobs")
    return {row[0] for row in cursor.fetchall()}


def mark_job_processed(
    conn: sqlite3.Connection,
    job_id: str,
    title: str,
    company: str,
    url: str,
    date_posted: str,
    matched: bool,
    site: str = "linkedin",
    location: str | None = None,
    is_remote: bool | None = None,
    reject_reason: str | None = None,
    seniority_level: str | None = None,
    employment_type: str | None = None,
    job_function: str | None = None,
    industry: str | None = None,
    salary: str | None = None,
    description: str | None = None,
    enrichment_json: str | None = None,
    score: int | None = None,
    tier: str | None = None,
    score_details_json: str | None = None,
    apply_url: str | None = None,
    ats_domain: str | None = None,
) -> None:
    # Сохраняем существующий user_status, apply_url, ats_domain, если запись обновляется
    cur = conn.execute(
        "SELECT user_status, apply_url, ats_domain FROM processed_jobs WHERE job_id = ?",
        (job_id,),
    ).fetchone()
    user_status = (cur["user_status"] if cur and cur["user_status"] else "new")
    existing_apply_url = cur["apply_url"] if cur else None
    existing_ats_domain = cur["ats_domain"] if cur else None

    final_apply_url = apply_url or existing_apply_url
    final_ats_domain = ats_domain or extract_root_domain(final_apply_url) or existing_ats_domain
    if not final_ats_domain and company:
        comp_info = get_company_ats_info(conn, company)
        if comp_info:
            final_ats_domain = comp_info.get("ats_domain")

    conn.execute(
        """
        INSERT OR REPLACE INTO processed_jobs (
            job_id, site, location, is_remote, title, company, url, date_posted,
            seniority_level, employment_type, job_function, industry, salary,
            description, matched, reject_reason, processed_at,
            enrichment_json, score, tier, score_details_json, user_status,
            apply_url, ats_domain
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_id,
            site or "linkedin",
            location,
            (1 if is_remote else 0) if is_remote is not None else None,
            title,
            company,
            url,
            date_posted,
            seniority_level,
            employment_type,
            job_function,
            industry,
            salary,
            description,
            1 if matched else 0,
            reject_reason,
            datetime.now(timezone.utc).isoformat(),
            enrichment_json,
            score,
            tier,
            score_details_json,
            user_status,
            final_apply_url,
            final_ats_domain,
        ),
    )
    conn.commit()


def update_job_enrichment_and_score(
    conn: sqlite3.Connection,
    job_id: str,
    enrichment: JobEnrichment,
    score_res: SkillScoreResult,
) -> None:
    reject_reason = None
    matched = 1
    if not score_res.geo_passed:
        matched = 0
        reject_reason = score_res.geo_reject_reason or "rejected_geo"
    elif score_res.score < 50:
        matched = 0
        reject_reason = f"low_score:{score_res.score}"

    conn.execute(
        """
        UPDATE processed_jobs
        SET enrichment_json = ?,
            score = ?,
            tier = ?,
            score_details_json = ?,
            matched = ?,
            reject_reason = COALESCE(?, reject_reason)
        WHERE job_id = ?
        """,
        (
            enrichment.model_dump_json(),
            score_res.score,
            score_res.tier,
            score_res.model_dump_json(),
            matched,
            reject_reason,
            job_id,
        ),
    )
    conn.commit()


def fetch_job_details(
    session: requests.Session,
    job_id: str,
    delay_range: tuple[float, float] = (1.5, 2.5),
    max_retries: int = 3,
) -> dict[str, str | None] | None:
    """
    Догружает полное описание вакансии и метаданные карточки (Seniority, Employment type,
    Job function, Industries, Salary) с паузой и ретраями при 429/502/503.
    """
    raw_id = job_id.removeprefix("li-")
    urls = [
        f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{raw_id}",
        f"https://www.linkedin.com/jobs/view/{raw_id}",
    ]

    for attempt in range(1, max_retries + 1):
        time.sleep(random.uniform(*delay_range))
        url = urls[(attempt - 1) % len(urls)]
        try:
            resp = session.get(url, headers=linkedin_headers, timeout=15)
            if resp.status_code == 200:
                if "authwall" in resp.url or "login" in resp.url:
                    print(f"  ⚠️ [{job_id}] Редирект на authwall (попытка {attempt}/{max_retries})")
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                div = soup.find("div", class_="show-more-less-html__markup")
                description = md(str(div)).strip() if div else ""

                salary_tag = soup.find("div", class_="compensation__salary")
                salary_text = " ".join(salary_tag.get_text().split()) if salary_tag else None
                apply_url = extract_linkedin_apply_url(soup)

                return {
                    "description": description,
                    "seniority_level": criteria(soup, "Seniority level"),
                    "employment_type": criteria(soup, "Employment type"),
                    "job_function": criteria(soup, "Job function"),
                    "industry": criteria(soup, "Industries"),
                    "salary": salary_text,
                    "apply_url": apply_url,
                }
            elif resp.status_code in (429, 502, 503, 504):
                backoff = attempt * 3.0 + random.uniform(1.0, 2.5)
                print(
                    f"  ⏳ [{job_id}] Статус {resp.status_code} (попытка {attempt}/{max_retries}), "
                    f"ждем {backoff:.1f}с..."
                )
                time.sleep(backoff)
            elif resp.status_code == 404:
                return {
                    "description": "",
                    "seniority_level": None,
                    "employment_type": None,
                    "job_function": None,
                    "industry": None,
                    "salary": None,
                    "apply_url": None,
                }
            else:
                print(f"  ⚠️ [{job_id}] Неожиданный статус {resp.status_code}")
        except requests.RequestException as e:
            backoff = attempt * 2.0
            print(f"  ⚠️ [{job_id}] Ошибка сети: {e} (попытка {attempt}/{max_retries}), ждем {backoff:.1f}с...")
            time.sleep(backoff)

    return None


def enrich_and_score_pending_jobs(
    conn: sqlite3.Connection,
    model: str = DEFAULT_MODEL,
    limit: int = 30,
    on_progress: Callable[[str], None] | None = None,
) -> int:
    """
    Находит в БД вакансии, прошедшие базовый фильтр (matched=1 и description IS NOT NULL),
    у которых еще нет enrichment_json, прогоняет их через локальный agy CLI (JobEnrichment)
    и оценивает по скиллу hirify-vacancy-filter.
    """
    def emit(msg: str) -> None:
        print(msg)
        if on_progress:
            on_progress(msg)

    rows = conn.execute(
        """
        SELECT job_id, title, company, url, date_posted, seniority_level, industry, salary, description
        FROM processed_jobs
        WHERE description IS NOT NULL
          AND description != ''
          AND enrichment_json IS NULL
          AND (reject_reason IS NULL OR reject_reason = '')
        ORDER BY processed_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    if not rows:
        emit("✨ Все кандидаты в базе уже обогащены через LLM.")
        return 0

    emit(f"🤖 Запуск LLM-обогащения ({model}) и скоринга для {len(rows)} вакансий...")
    enriched_count = 0

    for idx, row in enumerate(rows, start=1):
        job_id = row["job_id"]
        title = row["title"] or ""
        company = row["company"] or ""
        desc = row["description"] or ""

        emit(f"🧠 [{idx}/{len(rows)}] ИИ-разбор: {title} @ {company} ({job_id})...")
        try:
            enrichment = enrich_job_with_agy(
                title=title,
                company=company,
                location="EMEA / Remote",
                description=desc,
                model=model,
            )
            score_res = score_vacancy_by_skill(
                title=title,
                company=company,
                date_posted=row["date_posted"],
                seniority_level=row["seniority_level"],
                industry=row["industry"],
                salary_text=row["salary"],
                description=desc,
                enrichment=enrichment,
            )
            update_job_enrichment_and_score(conn, job_id, enrichment, score_res)
            enriched_count += 1
            badge = (
                "🟢 TOP"
                if score_res.match_category == "top"
                else "🟡 GOOD"
                if score_res.match_category == "good"
                else "🔴 LOW/GEO"
            )
            emit(
                f"  ↳ {badge} | Score: {score_res.score}/100 | {score_res.tier} | "
                f"Совпало: {len(score_res.matched_skills)}, Пробелов: {len(score_res.missing_skills)}"
            )
        except Exception as e:
            emit(f"  ⚠️ Ошибка LLM для {job_id}: {e}")

    return enriched_count


def fetch_and_filter_jobs(
    search_terms: str | list[str] = (
        "Agentic Engineer Remote",
        "AI Agent Engineer Remote",
        "Software Engineer Remote",
    ),
    site_names: list[str] | None = None,
    location: str = "EMEA",
    country_indeed: str = "uk",
    results_wanted: int = 30,
    hours_old: int = 4,
    easy_apply: bool | None = None,
    linkedin_company_ids: list[int] | None = None,
    run_llm_enrichment: bool = True,
    llm_model: str = DEFAULT_MODEL,
    llm_limit: int = 25,
    on_progress: Callable[[str], None] | None = None,
) -> list[dict]:
    def emit(msg: str) -> None:
        print(msg)
        if on_progress:
            on_progress(msg)

    conn = init_db()
    processed_ids = get_processed_ids(conn)
    emit(f"🗄️ В базе уже обработано вакансий: {len(processed_ids)}")

    if isinstance(search_terms, str):
        terms = [t.strip() for t in search_terms.split(",") if t.strip()]
    else:
        terms = list(search_terms)

    sites = [s.strip().lower() for s in (site_names or ["linkedin"]) if s.strip()]
    site = sites[0] if sites else "linkedin"

    # 1. Запрашиваем список вакансий по каждому запросу для выбранного провайдера
    frames: list[pd.DataFrame] = []
    easy_label = " [⚡ Только Easy Apply]" if easy_apply else ""

    for idx, term in enumerate(terms):
        if idx > 0:
            time.sleep(random.uniform(2.0, 4.0))

        # Для провайдеров с флагом is_remote=True убираем лишнее слово "Remote" из поисковой фразы,
        # чтобы не требовать буквального вхождения слова "Remote" в заголовок карточки
        clean_term = re.sub(r"\bremote\b", "", term, flags=re.IGNORECASE).strip() or term

        try:
            if site == "linkedin":
                emit(f"🔍 Поиск [linkedin] '{term}' в '{location}' (за последние {hours_old}ч){easy_label}...")
                df: pd.DataFrame = scrape_jobs(
                    site_name=["linkedin"],
                    search_term=term,
                    location=location,
                    results_wanted=results_wanted,
                    hours_old=hours_old,
                    easy_apply=easy_apply,
                    linkedin_company_ids=linkedin_company_ids,
                    fetch_description=False,
                )
            elif site == "indeed":
                # В Indeed база выбирается через country_indeed, а пустой location + is_remote=True
                # ищет все Remote-вакансии по всей выбранной стране без радиуса 50 миль вокруг точки
                target_country = (location or country_indeed or "uk").strip().lower()
                emit(
                    f"🔍 Поиск [indeed] '{clean_term}' (страна: {target_country.upper()}, Remote, за {hours_old}ч){easy_label}..."
                )
                df = scrape_jobs(
                    site_name=["indeed"],
                    search_term=clean_term,
                    location=None,
                    country_indeed=target_country,
                    is_remote=True,
                    results_wanted=results_wanted,
                    hours_old=hours_old,
                    easy_apply=easy_apply,
                    fetch_description=True,
                )
            elif site == "glassdoor":
                # В Glassdoor домен выбирается по country_indeed, а location передается как название страны/города
                gd_country_names = {
                    "uk": "United Kingdom",
                    "germany": "Germany",
                    "netherlands": "Netherlands",
                    "france": "France",
                    "spain": "Spain",
                    "ireland": "Ireland",
                    "switzerland": "Switzerland",
                    "austria": "Austria",
                    "belgium": "Belgium",
                    "italy": "Italy",
                    "usa": "United States",
                    "canada": "Canada",
                }
                target_country = (location or country_indeed or "uk").strip().lower()
                gd_loc = gd_country_names.get(target_country, location)
                emit(
                    f"🔍 Поиск [glassdoor] '{clean_term}' в '{gd_loc}' ({target_country.upper()}, Remote, за {hours_old}ч){easy_label}..."
                )
                df = scrape_jobs(
                    site_name=["glassdoor"],
                    search_term=clean_term,
                    location=gd_loc,
                    country_indeed=target_country,
                    is_remote=True,
                    results_wanted=results_wanted,
                    hours_old=hours_old,
                    easy_apply=easy_apply,
                    fetch_description=True,
                )
            elif site == "google":
                time_str = "since yesterday" if hours_old <= 24 else "in the last 3 days" if hours_old <= 72 else "in the last week"
                g_query = f"{clean_term} remote jobs in {location} {time_str}"
                emit(f"🔍 Поиск [google] '{g_query}'...")
                df = scrape_jobs(
                    site_name=["google"],
                    search_term=clean_term,
                    google_search_term=g_query,
                    location=location,
                    is_remote=True,
                    results_wanted=results_wanted,
                    hours_old=hours_old,
                    fetch_description=True,
                )
            elif site == "zip_recruiter":
                zr_loc = None if location.lower() in ("remote", "usa", "united states") else location
                emit(f"🔍 Поиск [zip_recruiter] '{clean_term}' в '{location}' (Remote, за {hours_old}ч){easy_label}...")
                df = scrape_jobs(
                    site_name=["zip_recruiter"],
                    search_term=clean_term,
                    location=zr_loc,
                    is_remote=True,
                    results_wanted=results_wanted,
                    hours_old=hours_old,
                    easy_apply=easy_apply,
                    fetch_description=True,
                )
            elif site == "hellowork":
                hw_loc = None if location.lower() in ("france", "remote", "télétravail") else location
                emit(f"🔍 Поиск [hellowork] '{clean_term}' в '{location}' (Télétravail, за {hours_old}ч)...")
                df = scrape_jobs(
                    site_name=["hellowork"],
                    search_term=clean_term,
                    location=hw_loc,
                    is_remote=True,
                    results_wanted=results_wanted,
                    hours_old=hours_old,
                    fetch_description=True,
                )
            elif site == "bayt":
                bayt_loc = None if location.lower() in ("all", "mena", "remote") else location
                emit(f"🔍 Поиск [bayt] '{clean_term}' в '{location}' (Remote, за {hours_old}ч){easy_label}...")
                df = scrape_jobs(
                    site_name=["bayt"],
                    search_term=clean_term,
                    location=bayt_loc,
                    is_remote=True,
                    results_wanted=results_wanted,
                    hours_old=hours_old,
                    easy_apply=easy_apply,
                    fetch_description=True,
                )
            else:
                emit(f"🔍 Поиск [{site}] '{clean_term}' в '{location}' (за {hours_old}ч)...")
                df = scrape_jobs(
                    site_name=[site],
                    search_term=clean_term,
                    location=location,
                    country_indeed=country_indeed,
                    is_remote=True,
                    results_wanted=results_wanted,
                    hours_old=hours_old,
                    easy_apply=easy_apply,
                    fetch_description=True,
                )

            site_errors = (df.attrs or {}).get("errors") or {}
            for err_site, err_msg in site_errors.items():
                emit(f"  ⚠️ [{err_site}] Сообщение провайдера: {err_msg}")

            if not df.empty:
                emit(f"  ↳ [{site}] Найдено по '{term}': {len(df)}")
                frames.append(df)
            else:
                emit(f"  ↳ [{site}] По '{term}' вакансий не найдено.")
        except Exception as e:
            emit(f"  ⚠️ [{site}] Ошибка поиска для '{term}': {e}")

    new_matches_count = 0
    if frames:
        jobs = pd.concat(frames, ignore_index=True)
        emit(f"📦 Суммарно карточек со всех запросов: {len(jobs)}")

        # 2. Дедупликация по job_id и по паре (title, company)
        jobs = jobs.drop_duplicates(subset=["id"]).copy()
        jobs["_dedup_key"] = (
            jobs["title"].fillna("").str.strip().str.lower()
            + "::"
            + jobs["company"].fillna("").str.strip().str.lower()
        )
        jobs = jobs.drop_duplicates(subset=["_dedup_key"]).drop(columns=["_dedup_key"]).copy()

        new_jobs_mask = ~jobs["id"].astype(str).isin(processed_ids)
        unseen_jobs = jobs[new_jobs_mask].copy()
        skipped_seen = len(jobs) - len(unseen_jobs)
        if skipped_seen:
            emit(f"⏭️ Пропущено уже обработанных ранее вакансий (из БД): {skipped_seen}")

        if not unseen_jobs.empty:
            # 3. Первичная фильтрация по заголовку ДО скачивания описания
            exclude_title_words = [
                "intern", "junior", "php", "c++", "wordpress", ".net", "c#", "golang", "rust", "ios", "macos", "android"
            ]
            exclude_pattern = "|".join(re.escape(w) for w in exclude_title_words)
            title_mask = ~unseen_jobs["title"].fillna("").str.lower().str.contains(exclude_pattern, regex=True)

            rejected_by_title = unseen_jobs[~title_mask]
            for _, row in rejected_by_title.iterrows():
                raw_loc = row.get("location")
                loc_str = str(raw_loc) if pd.notna(raw_loc) and raw_loc else None
                raw_rem = row.get("is_remote")
                is_rem_val = bool(raw_rem) if pd.notna(raw_rem) else None
                mark_job_processed(
                    conn,
                    job_id=str(row.get("id")),
                    site=str(row.get("site") or "linkedin"),
                    location=loc_str,
                    is_remote=is_rem_val,
                    title=str(row.get("title", "")),
                    company=str(row.get("company", "")),
                    url=str(row.get("job_url", "")),
                    date_posted=str(row.get("date_posted", "")),
                    matched=False,
                    reject_reason="excluded_title",
                )

            candidates = unseen_jobs[title_mask].copy()
            emit(
                f"🧹 Отсеяно по заголовку: {len(rejected_by_title)} | "
                f"Кандидатов для загрузки описания: {len(candidates)}"
            )

            # 4. Догружаем описания и критерии карточки (для LinkedIn с паузой 1.5–2.5 сек, для остальных берем из ответа)
            required_keywords = ["kotlin", "java", "spring", "python", "langgraph", "microservices", "llm", "agentic", "rag"]
            required_pattern = re.compile(
                r"\b(?:" + "|".join(re.escape(w) for w in required_keywords) + r")\b",
                re.IGNORECASE,
            )

            excluded_seniorities = {"internship", "entry level"}
            excluded_industries = {"staffing and recruiting"}

            session = requests.Session()

            for idx, (_, row) in enumerate(candidates.iterrows(), start=1):
                job_id = str(row.get("id"))
                site_val = str(row.get("site") or ("linkedin" if job_id.startswith("li-") else "other"))
                raw_loc = row.get("location")
                loc_str = str(raw_loc) if pd.notna(raw_loc) and raw_loc else None
                raw_rem = row.get("is_remote")
                is_rem_val = bool(raw_rem) if pd.notna(raw_rem) else None
                title = str(row.get("title", ""))
                company = str(row.get("company", ""))
                job_url = str(row.get("job_url", ""))
                date_posted = str(row.get("date_posted", ""))

                if site_val == "linkedin" or job_id.startswith("li-"):
                    emit(f"📥 [{idx}/{len(candidates)}] [linkedin] Загрузка карточки: {title} @ {company} ({job_id})...")
                    details = fetch_job_details(session, job_id)
                    if details is None:
                        emit(f"  ❌ Не удалось загрузить карточку {job_id}, оставляем на следующий запуск.")
                        continue
                    description = details["description"] or ""
                    seniority = details["seniority_level"]
                    employment_type = details["employment_type"]
                    job_function = details["job_function"]
                    industry = details["industry"]
                    salary = details["salary"]
                    apply_url = details.get("apply_url")
                else:
                    emit(f"📥 [{idx}/{len(candidates)}] [{site_val}] Обработка карточки: {title} @ {company} ({job_id})...")
                    raw_desc = row.get("description")
                    description = str(raw_desc) if pd.notna(raw_desc) and raw_desc else ""
                    raw_level = row.get("job_level")
                    seniority = str(raw_level) if pd.notna(raw_level) and raw_level else None
                    raw_type = row.get("job_type")
                    employment_type = str(raw_type) if pd.notna(raw_type) and raw_type else None
                    raw_func = row.get("job_function")
                    job_function = str(raw_func) if pd.notna(raw_func) and raw_func else None
                    raw_ind = row.get("company_industry")
                    industry = str(raw_ind) if pd.notna(raw_ind) and raw_ind else None
                    raw_direct = row.get("job_url_direct")
                    apply_url = str(raw_direct) if pd.notna(raw_direct) and raw_direct else None

                    min_amt = row.get("min_amount")
                    max_amt = row.get("max_amount")
                    curr = row.get("currency") or "$"
                    interval = row.get("interval") or "yr"
                    if pd.notna(min_amt) and pd.notna(max_amt) and (min_amt or max_amt):
                        salary = f"{curr}{min_amt:,.0f} - {curr}{max_amt:,.0f}/{interval}"
                    else:
                        salary = None

                reject_reason = None
                if seniority and seniority.strip().lower() in excluded_seniorities:
                    reject_reason = f"excluded_seniority:{seniority}"
                elif industry and industry.strip().lower() in excluded_industries:
                    reject_reason = f"excluded_industry:{industry}"
                elif not required_pattern.search(description):
                    reject_reason = "missing_keywords"

                is_match = reject_reason is None

                mark_job_processed(
                    conn,
                    job_id=job_id,
                    site=site_val,
                    location=loc_str,
                    is_remote=is_rem_val,
                    title=title,
                    company=company,
                    url=job_url,
                    date_posted=date_posted,
                    matched=is_match,
                    reject_reason=reject_reason,
                    seniority_level=seniority,
                    employment_type=employment_type,
                    job_function=job_function,
                    industry=industry,
                    salary=salary,
                    description=description,
                    apply_url=apply_url,
                )

                if is_match:
                    new_matches_count += 1
                    emit(f"  ✅ Прошла базовый фильтр ({seniority or 'N/A'} | {industry or 'N/A'})")
                else:
                    emit(f"  ➖ Отклонено ({reject_reason}).")
        else:
            emit("Все найденные карточки из поиска уже были в БД.")
    else:
        emit("Поисковая выдача пуста.")

    # 5. Запускаем Шаг 1 (JobEnrichment через agy CLI) + Шаг 2 (Скоринг по скиллу) только если появились новые кандидаты
    if run_llm_enrichment:
        if new_matches_count > 0:
            enrich_and_score_pending_jobs(conn, model=llm_model, limit=llm_limit, on_progress=on_progress)
        else:
            emit("⏭️ Новых кандидатов для ИИ-оценки не появилось — запуск LLM пропущен.")

    # Возвращаем отранжированный сухой остаток
    final_rows = conn.execute(
        """
        SELECT * FROM processed_jobs
        WHERE matched = 1 AND score IS NOT NULL AND score >= 50
        ORDER BY score DESC, date_posted DESC
        """
    ).fetchall()
    results = [dict(r) for r in final_rows]
    conn.close()
    return results


if __name__ == "__main__":
    matched = fetch_and_filter_jobs()
    print(f"\n🎯 Итого вакансий в сухом остатке (Score >= 50): {len(matched)}\n")
    for job in matched:
        print(f"🔥 [{job.get('score')}/100 | {job.get('tier')}] {job['title']} @ {job['company']} ({job['date_posted']})")
        print(f"🔗 {job['url']}\n")
