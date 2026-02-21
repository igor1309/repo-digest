# Repo Digest Log

## 21.02.2026

- Fix weekly releases workflow secret mapping with fallbacks to existing repo secrets (`GH_PAT`, `TELEGRAM_TOKEN`).
- Rename repo from `weekend-issues-digest` to `repo-digest` and update README for both workflows (schedule, triggers, purpose, secrets).
- Harden release-digest script: require `GH_TOKEN`, validate lookback days as positive integer, and paginate releases per repository.
- Add weekly releases workflow schedule at 07:55 MSK (04:55 UTC) and make default lookback configurable (`DAYS_DEFAULT`, default 7).

## 01.02.2026

Update repo list.
Add scripts to list updated private repos and diff.

## 24.01.2026

Update the log to record the repo update and prevent disabling GitHub Actions due to 60 days of inactivity. Enable GitHub Action.

## 30.08.2025

- implemented the GitHub Actions workflow and Python script for the digest
- add repo `weekend-issues-digest`, add bot secrets, repo list
- create WeekendIssuesDigestBot
- define specs, create repo with README and SPEC
- define the pain, discuss with ChatGPT (original.md)
