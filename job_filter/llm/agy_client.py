"""Единый клиент для локального `agy` CLI: запуск модели и извлечение JSON из ответа."""
import json
import logging
import re
import subprocess
import time

from job_filter import config

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
    """Ошибка вызова LLM или разбора её ответа."""


def run_agy(
    prompt: str,
    model: str | None = None,
    timeout_sec: int = 90,
    json_schema: dict | None = None,
) -> str:
    """Запускает `agy -p <prompt>` и возвращает stdout.

    Если передан json_schema — включается структурированный вывод (`--output-format json --json-schema`).
    """
    model = model or config.DEFAULT_MODEL
    cmd = [config.AGY_BIN, "--model", model, "--disable-slash-commands"]
    if json_schema is not None:
        cmd += ["--output-format", "json", "--json-schema", json.dumps(json_schema)]
    cmd += ["-p", prompt]

    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
    except subprocess.TimeoutExpired as e:
        raise LLMError(f"agy timed out after {timeout_sec}s") from e
    duration = time.time() - t0

    if proc.returncode != 0:
        err_msg = (proc.stderr or proc.stdout or "").strip()[:400]
        logger.error("agy (%s) failed in %.1fs: %s", model, duration, err_msg)
        raise LLMError(f"agy exited with {proc.returncode}: {err_msg}")

    raw = (proc.stdout or "").strip()
    if not raw:
        raise LLMError("agy returned empty response")
    logger.info("agy (%s) responded in %.1fs, %d chars", model, duration, len(raw))
    return raw


def unwrap_structured_output(envelope: dict) -> dict:
    """Достаёт полезную нагрузку из JSON-конверта `agy --output-format json`."""
    if envelope.get("structured_output"):
        return envelope["structured_output"]
    if isinstance(envelope.get("response"), str):
        return extract_json_object(envelope["response"])
    return envelope


def extract_json_object(text: str) -> dict:
    text = text.strip()
    # 1. Сначала пробуем распарсить как есть
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    # 2. Ищем markdown-блок ```json ... ``` или ``` ... ```
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if fence:
        candidate = fence.group(1).strip()
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(candidate[start : end + 1])
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass

    # 3. Ищем самый внешний блок от первого { до последнего }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            parsed = json.loads(text[start : end + 1])
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    # 4. Если вывод содержит несколько строк NDJSON или построчный вывод, ищем последнюю валидную JSON-строку
    for line in reversed(text.splitlines()):
        line_s = line.strip()
        if line_s.startswith("{") and line_s.endswith("}"):
            try:
                parsed = json.loads(line_s)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                continue

    raise ValueError("Не удалось обнаружить валидный JSON-объект в ответе модели")
