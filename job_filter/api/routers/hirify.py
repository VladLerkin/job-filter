"""Роуты взаимодействия с Hirify API (сохраненные фильтры / feeds, статус квот)."""
import logging
from fastapi import APIRouter
from job_filter.scraping.hirify_adapter import HirifyClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/hirify", tags=["hirify"])


@router.get("/feeds")
def get_hirify_feeds():
    """Возвращает список сохраненных фильтров пользователя и статус активности."""
    client = HirifyClient()
    if not client.is_configured():
        return {
            "configured": False,
            "message": "HIRIFY_API_KEY не установлен.",
            "feeds": [],
        }

    try:
        feeds = client.get_feeds()
        return {
            "configured": True,
            "feeds": feeds,
        }
    except Exception as e:
        logger.error("Ошибка при получении фильтров Hirify: %s", e)
        return {
            "configured": True,
            "error": str(e),
            "feeds": [],
        }

