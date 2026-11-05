"""Централизованная конфигурация приложения.

Все пути, параметры LLM, пороги скоринга и правила первичной фильтрации собраны здесь.
Значения можно переопределить переменными окружения (JOB_FILTER_DB, AGY_BIN, JOB_FILTER_MODEL).
"""
import os
import shutil
from pathlib import Path

# --- Пути ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_env_file(path: Path) -> None:
    """Загружает переменные из .env файла в os.environ, если они ещё не заданы."""
    if not path.is_file():
        return
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip("'\"")
            if k and k not in os.environ:
                os.environ[k] = v
    except Exception:
        pass


_load_env_file(PROJECT_ROOT / ".env")

APP_VERSION = "1.1.0"
DB_PATH = Path(os.getenv("JOB_FILTER_DB", PROJECT_ROOT / "jobs.db"))
STATIC_DIR = PROJECT_ROOT / "static"

# --- LLM (agy CLI) ---
AGY_BIN = os.getenv("AGY_BIN") or shutil.which("agy") or str(Path.home() / ".local" / "bin" / "agy")
DEFAULT_MODEL = os.getenv("JOB_FILTER_MODEL", "gemini-3.8-flash-low")
JOB_ENRICH_TIMEOUT_SEC = 90
CV_ANALYZE_TIMEOUT_SEC = 120

# --- Hirify Agent API ---
HIRIFY_API_KEY = os.getenv("HIRIFY_API_KEY", "")
HIRIFY_API_URL = os.getenv("HIRIFY_API_URL", "https://api.hirify.me/api/agent")

# --- Пороги скоринга ---
TOP_SCORE_THRESHOLD = 70
GOOD_SCORE_THRESHOLD = 50

# --- Связка «последняя открытая вакансия» -> ATS (сек.) ---
LAST_OPENED_TTL_SEC = 1800

# --- Первичная фильтрация вакансий (до LLM) ---
EXCLUDED_TITLE_WORDS = (
    "intern", "junior", "php", "c++", "wordpress", ".net", "c#", "golang", "rust", "ios", "macos", "android",
)
REQUIRED_DESCRIPTION_KEYWORDS = (
    "kotlin", "java", "spring", "python", "langgraph", "microservices", "llm", "agentic", "rag",
)
EXCLUDED_SENIORITIES = frozenset({"internship", "entry level"})
EXCLUDED_INDUSTRIES = frozenset({"staffing and recruiting"})

DEFAULT_SEARCH_TERMS = (
    "Agentic Engineer Remote",
    "AI Agent Engineer Remote",
    "Software Engineer Remote",
)

