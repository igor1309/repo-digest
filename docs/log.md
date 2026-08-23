# Repo Digest Log

## 23.08.2026

- Add GitHub CLI-first repository instructions and a `CLAUDE.md` symlink so GitHub Actions maintenance starts from live repository state.

## 01.03.2026

- Migrate all Telegram sends to ci-shared `notify_telegram.sh` transport (3 scripts, 2 languages → 1 bash wrapper). Eliminates duplicated HTTP/retry logic across Node.js, Python, and embedded-Python call sites.
- Split weekend issues digest into multiple Telegram messages when content exceeds the 4000-char limit, using continuation headers to keep context across chunks.
- Add unit tests for digest chunking, escaping, and title clamping; extend test runner to cover Python tests.

## 21.02.2026

- Sort grouped release bullets by semantic version in descending order (for tags like `v0.15.10`) so Telegram output stays naturally ordered within each repository section.
- Group weekly release digest rows by repository with italic repo headers and blank section separators, removing repeated `owner/repo` text on every bullet.
- Make each weekly release bullet a single clickable version/date link (`vX.Y.Z (YYYY-MM-DD)`) and add regression coverage for grouped rendering.
- Stop truncating weekly release digests by splitting long outputs into multiple Telegram messages with continuation headers.
- Fix Telegram HTML parsing failures in weekly release runs by switching to line-safe truncation that never cuts message tags.
- Add regression coverage for Telegram message rendering/truncation so future formatting changes cannot reintroduce invalid HTML payloads.
- Add a dedicated CI workflow that runs on each push and on pull requests to `trunk`, so test regressions are blocked before release automation.
- Standardize test execution around one shared command (`./scripts/run_silent.sh "tests" ./scripts/test.sh`) for both local and CI runs.
- Vendor and pin `ci-shared` run wrapper to a fixed commit, reducing drift and keeping test output compact but debuggable.
- Improve weekly release message header readability with period-aware formatting and context-aware title (`Releases this week` vs `Releases in ...`).
- Render release message header in bold in Telegram using HTML parse mode for clearer scanability.
- Add focused automated coverage for period formatting and header selection rules to prevent future formatting regressions.
- Compact weekly release digest items into single clickable links in Telegram to reduce message length and improve scanability.
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
