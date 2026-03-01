#!/usr/bin/env bash
# vendored-from-repo: https://github.com/igor1309/ci-shared
# vendored-from-path: scripts/notify_telegram.sh
# vendored-from-commit: 42d4684c0968e7a147b52ac6589271e571da2bed
# vendored-on: 2026-03-01
# vendored-note: includes TELEGRAM_PARSE_MODE / TELEGRAM_DISABLE_PREVIEW
#   support ahead of upstream (ci-shared#4).
#
# Telegram transport: send one or more message chunks to a bot/chat.
# Chunks are delivered sequentially in argument order. Fail-fast on
# first error; partial delivery is accepted.
#
# Usage: notify_telegram.sh <token> <chat_id> <chunk1> [chunk2...]
#
# Environment variables (optional):
#   TELEGRAM_PARSE_MODE      – "HTML", "MarkdownV2", or "Markdown".
#                               Omit for plain text (Telegram default).
#   TELEGRAM_DISABLE_PREVIEW – set to "true" to suppress link previews.
#
# Caller is responsible for message formatting, splitting, and
# choosing which bot/chat to use.
set -euo pipefail

if [ "$#" -lt 3 ]; then
  echo "usage: notify_telegram.sh <token> <chat_id> <chunk1> [chunk2...]" >&2
  exit 2
fi

token="$1"
chat_id="$2"
shift 2

extra_args=()
if [ -n "${TELEGRAM_PARSE_MODE:-}" ]; then
  extra_args+=(--data-urlencode "parse_mode=${TELEGRAM_PARSE_MODE}")
fi
if [ "${TELEGRAM_DISABLE_PREVIEW:-}" = "true" ]; then
  extra_args+=(--data-urlencode "disable_web_page_preview=true")
fi

for chunk in "$@"; do
  curl -fsS --connect-timeout 5 --max-time 20 \
    --retry 3 --retry-delay 1 --retry-all-errors \
    -X POST "https://api.telegram.org/bot${token}/sendMessage" \
    -d "chat_id=${chat_id}" \
    --data-urlencode "text=${chunk}" \
    "${extra_args[@]}"
done
