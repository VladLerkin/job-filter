#!/bin/zsh
cd "$(dirname "$0")" || exit 1

PORT=8000
URL="http://localhost:${PORT}"

echo "🚀 Запуск Job Filter на ${URL} ..."

# Автоматически открываем браузер через 1.5 секунды после старта сервера
(sleep 1.5 && open "${URL}") &

exec .venv/bin/python -m uvicorn app:app --reload --port "${PORT}"

