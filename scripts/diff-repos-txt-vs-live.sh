#!/usr/bin/env bash
# Diffs repos.txt against live GitHub output from list-updated-private-repos.sh.
set -euo pipefail

since_date="${1:-}"
list_script="scripts/list-updated-private-repos.sh"
repos_file="repos.txt"

if [ -z "$since_date" ]; then
  live_output="$("$list_script")"
else
  live_output="$("$list_script" "$since_date")"
fi

live_names="$(printf '%s\n' "$live_output" | awk -F'\t' '{print $1}' | sort)"
tracked_names="$(grep -v '^[[:space:]]*$' "$repos_file" | sort)"

missing_in_repos_txt="$(comm -23 <(printf '%s\n' "$live_names") <(printf '%s\n' "$tracked_names"))"

echo "Missing from repos.txt:"
if [ -n "$missing_in_repos_txt" ]; then
  printf '%s\n' "$missing_in_repos_txt"
else
  echo "(none)"
fi
