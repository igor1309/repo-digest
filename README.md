# Repo Digest

![bot_icon](bot_icon.JPG)

**Telegram digests for private GitHub repositories: weekend open issues and weekly releases.**

This repository contains personal automations that run on schedule and post structured reports to Telegram.

## Workflows

### Weekend issues digest

Workflow: `.github/workflows/digest.yml`

- Schedule: Saturday and Sunday at `04:15 UTC` (`07:15 MSK`).
- Trigger: scheduled and manual (`workflow_dispatch`).
- Purpose: fetch open issues from repositories in `repos.txt` and send a weekend digest to Telegram.
- Secrets: `GH_PAT`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`.

### Weekly releases to Telegram

Workflow: `.github/workflows/weekly-releases-to-telegram.yml`

- Schedule: Saturday at `04:55 UTC` (`07:55 MSK`).
- Trigger: scheduled and manual (`workflow_dispatch`) with optional inputs `days` and `includePrereleases`.
- Purpose: fetch releases published in the lookback window and send a release digest to Telegram.
- Secrets: `GH_TOKEN` (or `GH_PAT`), `TELEGRAM_BOT_TOKEN` (or `TELEGRAM_TOKEN`), `TELEGRAM_CHAT_ID`.

## Setup

To run these automations, configure:

- A list of your target GitHub repositories in `repos.txt` (keep it sorted).
- Credentials for the GitHub API and Telegram bot(s) required by each workflow.
- A scheduled environment to execute the script.

For all implementation details, message formats, and specific configuration values, please refer to **[SPEC.md](docs/SPEC.md)**, which is the single source of truth.

## Testing

Run tests via the stable wrapper:

```bash
./scripts/run_silent.sh "tests" ./scripts/test.sh
```

`scripts/run_silent.sh` delegates to `vendor/ci-shared/scripts/run_silent.sh`, pinned to a specific `ci-shared` commit.

## Scripts

### Weekly releases to Telegram

`scripts/weekly_releases.mjs` queries GitHub GraphQL for releases and posts a digest to Telegram.

- Filters to releases whose `publishedAt` is within the last N days (default `7`).
- Skips drafts and, by default, prereleases. You can include prereleases via manual workflow trigger input.
- Scans only repositories where you are `OWNER` (personal repos). If needed, this can be extended to include org repositories you are a member of.
- Requires `GH_TOKEN` (the script does not fall back to `GITHUB_TOKEN`).
- Paginates releases per repository to avoid missing recent releases in high-activity repos.

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

### Notify missing repos

`scripts/notify-missing-repos.sh` runs the diff and sends a Telegram MarkdownV2 message when `repos.txt` is missing any live repos. It does not block the digest.

Usage:

```
scripts/notify-missing-repos.sh 2025-01-01
```

Dry run (prints the message instead of sending):

```
scripts/notify-missing-repos.sh --dry-run 2025-01-01
```
