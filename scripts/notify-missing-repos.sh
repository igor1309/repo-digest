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

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

# MarkdownV2: escape special characters in dynamic text.
escape_mdv2() {
  printf '%s' "$1" | sed 's/[][\\_.*()`~>#+=|{}!-]/\\&/g'
}

# Build message
header="*$(escape_mdv2 'Missing repos in repos.txt')*"
body=""
while IFS= read -r repo; do
  [ -z "$repo" ] && continue
  body="${body}
\\- $(escape_mdv2 "$repo")"
done <<< "$missing_list"

message="${header}${body}"

if [ "$dry_run" = "1" ]; then
  printf '%s\n' "$message"
  exit 0
fi

token="${TELEGRAM_TOKEN:-}"
chat_id="${TELEGRAM_CHAT_ID:-}"
if [ -z "$token" ] || [ -z "$chat_id" ]; then
  echo "Missing Telegram configuration. Skipping notification." >&2
  exit 0
fi

TELEGRAM_PARSE_MODE=MarkdownV2 TELEGRAM_DISABLE_PREVIEW=true \
  "$script_dir/ci/notify_telegram.sh" "$token" "$chat_id" "$message"
