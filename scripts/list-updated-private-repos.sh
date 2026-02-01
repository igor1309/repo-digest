#!/usr/bin/env bash
# Lists private, non-archived repos updated since a date for your user and orgs.
# Output is tab-separated and sorted by most recently updated.
set -euo pipefail

since_date="${1:-}"
if [ -z "$since_date" ]; then
  since_date="2025-01-01"
fi
cutoff="${since_date}T00:00:00Z"

list_owner() {
  local owner
  owner="$1"
  GH_PAGER=cat gh repo list "$owner" --visibility private --no-archived --limit 1000 --json nameWithOwner,updatedAt --jq ".[] | select(.updatedAt >= \"${cutoff}\") | \"\(.nameWithOwner)\t\(.updatedAt)\""
}

user_login="$(GH_PAGER=cat gh api /user --jq '.login')"
org_logins="$(GH_PAGER=cat gh api --paginate /user/orgs --jq '.[].login')"

{
  if ! list_owner "$user_login"; then
    echo "Failed to list repos for: ${user_login}" >&2
  fi
  while IFS= read -r org_login; do
    if [ -n "$org_login" ]; then
      if ! list_owner "$org_login"; then
        echo "Failed to list repos for: ${org_login}" >&2
      fi
    fi
  done <<< "$org_logins"
} | sort -r -k2
