#!/usr/bin/env bash
# Notify via Telegram when repos.txt is missing live repos.
set -euo pipefail

dry_run="0"
if [ "${1:-}" = "--dry-run" ] || [ "${1:-}" = "-n" ]; then
  dry_run="1"
  shift
fi

since_date="${1:-2025-01-01}"

if ! diff_output="$(scripts/diff-repos-txt-vs-live.sh "$since_date")"; then
  echo "Repo diff failed. Skipping notification."
  exit 0
fi

missing_list="$(printf '%s\n' "$diff_output" | awk 'NR>1 && $0 != "(none)" && $0 !~ /^[[:space:]]*$/')"

if [ -z "$missing_list" ]; then
  echo "No missing repos detected."
  exit 0
fi

DRY_RUN="$dry_run" MISSING_LIST="$missing_list" python - <<'PY'
import os
import re
import requests
import sys

def escape_markdown_v2(text):
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))

token = os.environ.get("TELEGRAM_TOKEN")
chat_id = os.environ.get("TELEGRAM_CHAT_ID")
dry_run = os.environ.get("DRY_RUN") == "1"
missing_raw = os.environ.get("MISSING_LIST", "")

missing_items = [line.strip() for line in missing_raw.splitlines() if line.strip()]
if not missing_items:
    print("Missing list was empty after parsing. Skipping notification.")
    sys.exit(0)

header = f"*{escape_markdown_v2('Missing repos in repos.txt')}*"
lines = [f"\\- {escape_markdown_v2(repo)}" for repo in missing_items]
message = "\n".join([header, *lines])

if dry_run:
    print(message)
    sys.exit(0)

if not token or not chat_id:
    print("Missing Telegram configuration. Skipping notification.", file=sys.stderr)
    sys.exit(0)

url = f"https://api.telegram.org/bot{token}/sendMessage"
payload = {
    "chat_id": chat_id,
    "text": message,
    "parse_mode": "MarkdownV2",
    "disable_web_page_preview": True,
}

try:
    response = requests.post(url, json=payload, timeout=15)
    if response.status_code >= 400:
        print(f"Telegram API error: {response.status_code} {response.text}", file=sys.stderr)
except requests.RequestException as exc:
    print(f"Failed to send Telegram message: {exc}", file=sys.stderr)
PY
