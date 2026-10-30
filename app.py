"""Точка входа uvicorn для запуска приложения (`uvicorn app:app`).

Все маршруты, зависимости и сервисы вынесены в модульный пакет `job_filter`.
"""
from job_filter.api.app import app, create_app

__all__ = ["app", "create_app"]
