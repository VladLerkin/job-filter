#!/bin/zsh
cd "$(dirname "$0")" || exit 1

# Автоматически загружаем переменные из .env, если файл существует
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

PORT=8000
URL="http://localhost:${PORT}"

echo "🚀 Запуск Job Filter на ${URL} ..."

# Автоматически открываем браузер через 1.5 секунды после старта сервера
(sleep 1.5 && open "${URL}") &

exec .venv/bin/python -m uvicorn app:app --reload --port "${PORT}"

