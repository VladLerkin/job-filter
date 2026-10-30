"""Управление запуском фонового потока поиска/обогащения и стримингом логов в веб-интерфейс."""
import logging
import threading
import time
from typing import Any

from job_filter.db.connection import connect
from job_filter.services.pipeline import enrich_and_score_pending_jobs, fetch_and_filter_jobs

logger = logging.getLogger(__name__)


class PipelineRunner:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._running = False
        self._logs: list[str] = []
        self._started_at: str | None = None
        self._finished_at: str | None = None

    def append_log(self, msg: str) -> None:
        ts = time.strftime("%H:%M:%S")
        with self._lock:
            self._logs.append(f"[{ts}] {msg}")

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def get_status(self, since: int = 0) -> dict[str, Any]:
        with self._lock:
            return {
                "running": self._running,
                "started_at": self._started_at,
                "finished_at": self._finished_at,
                "logs": self._logs[since:],
                "next_index": len(self._logs),
            }

    def start(self, req_data: dict[str, Any]) -> bool:
        with self._lock:
            if self._running:
                return False
            self._running = True
            self._logs = []
            self._started_at = time.strftime("%Y-%m-%d %H:%M:%S")
            self._finished_at = None

        thread = threading.Thread(target=self._worker, args=(req_data,), daemon=True)
        thread.start()
        return True

    def _worker(self, req: dict[str, Any]) -> None:
        try:
            if req.get("enrich_only"):
                conn = connect()
                try:
                    enrich_and_score_pending_jobs(
                        conn,
                        model=req.get("llm_model"),
                        limit=req.get("llm_limit", 15),
                        on_progress=self.append_log,
                    )
                finally:
                    conn.close()
            else:
                fetch_and_filter_jobs(
                    search_terms=req.get("search_terms"),
                    site_names=req.get("site_names"),
                    location=req.get("location", "EMEA"),
                    country_indeed=req.get("country_indeed", "uk"),
                    results_wanted=req.get("results_wanted", 20),
                    hours_old=req.get("hours_old", 4),
                    easy_apply=True if req.get("easy_apply") else None,
                    run_llm_enrichment=True,
                    llm_model=req.get("llm_model"),
                    llm_limit=req.get("llm_limit", 15),
                    on_progress=self.append_log,
                )
            self.append_log("✅ Пайплайн успешно завершен!")
        except Exception as e:
            logger.exception("Pipeline execution failed: %s", e)
            self.append_log(f"❌ Ошибка выполнения пайплайна: {e}")
        finally:
            with self._lock:
                self._running = False
                self._finished_at = time.strftime("%Y-%m-%d %H:%M:%S")


pipeline_runner = PipelineRunner()

