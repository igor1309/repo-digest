---
date: 2026-02-01
model: gpt-5.2
description: "Project overview and usage notes for helper scripts."
---

# Weekend Issues Digest

![bot_icon](bot_icon.JPG)

**Weekend snapshot of open issues from your private GitHub repositories delivered to your Telegram bot.**

This is a simple personal automation that runs on a schedule to fetch open issues from your GitHub repositories and post a structured report to a Telegram chat. The report groups repositories with open issues, lists the newest issues for each, and summarizes the rest. Repositories with no open issues are listed separately.

## Setup

To run this automation, you will need to configure:

- A list of your target GitHub repositories in `repos.txt` (keep it sorted).
- Credentials for the GitHub API and a Telegram bot.
- A scheduled environment to execute the script.

For all implementation details, message formats, and specific configuration values, please refer to **[SPEC.md](docs/SPEC.md)**, which is the single source of truth.

## Scripts

### List updated private repos

`scripts/list-updated-private-repos.sh` outputs private, non-archived repositories updated since a given date for your user and orgs you belong to. Output is tab-separated and sorted by most recently updated.

Usage:

```
scripts/list-updated-private-repos.sh 2025-01-01
```

If the date is omitted, it defaults to `2025-01-01`.

### Diff repos.txt vs live list

`scripts/diff-repos-txt-vs-live.sh` compares `repos.txt` against the live list produced by `scripts/list-updated-private-repos.sh` and prints what is missing from `repos.txt`.

Usage:

```
scripts/diff-repos-txt-vs-live.sh 2025-01-01
```

If the date is omitted, it uses the default from `scripts/list-updated-private-repos.sh`.
