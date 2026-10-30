"""Роут отдачи главной страницы веб-интерфейса."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from job_filter import config

router = APIRouter(tags=["ui"])

INDEX_HTML_PATH = config.STATIC_DIR / "index.html"


@router.get("/", response_class=HTMLResponse)
def index():
    if INDEX_HTML_PATH.is_file():
        return INDEX_HTML_PATH.read_text(encoding="utf-8")
    return "<h1>UI file not found</h1>"
