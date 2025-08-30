# Weekend Issues Digest

**Tagline:** Weekly (weekend) snapshot of open issues from your private GitHub repositories delivered to your Telegram bot.

—

## Overview
**Weekend Issues Digest** is a small, personal automation that runs on **Saturdays and Sundays at 07:15 MSK** and sends a structured Markdown report to a Telegram chat.  
The report lists **all open issues** for a predetermined set of private repositories. The list of repositories is stored in a simple, editable artifact (`repos.txt`) so you can add or remove repos without changing the automation.

This project is intentionally minimal — no scale, no UI, low operational burden.

—

## What it does (short)
- Reads `repos.txt` (one `owner/repo` per line) from the automation repository root.  
- For each repo, fetches **open issues**, sorts by **created date (newest first)**, and lists up to **10** issues. If there are more than 10 open issues, the digest shows `and N more issues`.  
- Builds a single **legacy Markdown** message and posts it to your Telegram bot. If message length > 4096 characters, it splits by repo sections.

—

## Prerequisites
- A GitHub repository to host the automation and `repos.txt` (you told me it exists).
- A Personal Access Token (PAT) with permissions to read your private repos.
- A Telegram bot token and the chat ID where messages will be posted.
- Workflow runner (recommended: GitHub Actions in the automation repo).

—

## Files & configuration
- **`repos.txt`** — required. Plain text file at repo root, one `owner/repo` per line. Editable via GitHub UI.
  ```
  youruser/project-one
  youruser/project-two
  ```
- **Secrets** (store in GitHub Secrets)
  - `GH_PAT` — personal access token (minimum `repo` read scope).  
  - `TELEGRAM_TOKEN` — your bot token.  
  - `TELEGRAM_CHAT_ID` — numeric chat id or channel id.

—

## Schedule
The workflow should be scheduled for **04:15 UTC** on **Saturday** and **Sunday** (this equals **07:15 MSK**). Add a manual `workflow_dispatch` trigger for testing.

—

## Message format
Messages use **legacy Telegram Markdown**. The structure per run:

```
# Weekend issues report — Sat, 2025-09-06

## owner/repo-1
1. Issue title (clamped to 18 words) — #123 — 2025-09-05 — @author — https://github.com/owner/repo-1/issues/123
...
and 7 more issues

## owner/repo-2
No open issues.
```

Rules:
- **Titles** clamped to **18 words** (count words, append `…` if truncated).  
- **Sort** by `created_at` descending.  
- **Limit** 10 displayed issues per repo; compute overflow as `total_open - 10`.  
- **Character limit:** Telegram messages must be ≤ 4096 chars. If needed, split into multiple messages by repo sections and avoid breaking a repo section unless necessary.

—

## Edge cases & behavior
- Titles containing Markdown-sensitive characters are **minimally sanitized** (remove or neutralize problematic backticks and unmatched brackets/parentheses) to avoid rendering issues. Legacy Markdown is more forgiving than MarkdownV2; do not apply V2 escaping.  
- If a repo has **0 open issues** show `No open issues.`  
- If a single repo section alone exceeds 4096 chars (unlikely), split the repo across messages between items.  
- On transient API/network errors, retry a couple of times. On persistent failure, send a short failure message to Telegram:  
  `Weekend issues report — FAILED: <short error summary>`

—

## Deployment checklist (no code)
1. Add `repos.txt` to the automation repo root and commit.  
2. Add secrets in repository settings → Secrets: `GH_PAT`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`.  
3. Add a scheduled workflow (recommended GitHub Actions) running at 04:15 UTC on Sat & Sun and supporting manual dispatch. The workflow should:
   - Read `repos.txt`.  
   - For each repo fetch open issues sorted by created date desc.  
   - Build Markdown message(s) per the Message format rules.  
   - Post to Telegram using the bot token/chat id.  
   - On fatal error, post a short failure message.  
4. Test via manual dispatch and verify Telegram output. Adjust sanitization if necessary.

—

## Testing tips
- Use 2–3 repos with different issue volumes and titles containing special characters.  
- Verify the clamping (18 words), `and N more issues` display, and proper sorting.  
- Test message splitting by creating many issues (or mocking) to exceed the Telegram limit and ensure split logic works.

—

## Security & maintenance
- Keep `GH_PAT` narrow-scoped and rotate periodically.  
- Keep secrets in GitHub Secrets only. Do not print secrets in logs or messages.  
- Keep `repos.txt` under version control to audit changes.  
- If you later need per-repo metadata, migrate to `repos.yaml`.

—

## Troubleshooting
- **No message received:** check `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID` correctness, and verify workflow logs.  
- **Formatting issues:** inspect issue titles for Markdown tokens; tighten sanitization.  
- **Auth errors:** ensure `GH_PAT` has appropriate repo read scope and is not expired.

—

## Name & branding
Project name: **Weekend Issues Digest** — chosen for clarity and minimal ambiguity.  
Short description for README header or Telegram tagline: _Weekend snapshot of open issues from your private repos_.

—

## License
MIT — minimal, permissive.

—

## Contributing & changelog
This project is a personal automation. If you keep it public, use PRs to update `repos.txt`. For personal forks or changes, edit `repos.txt` directly in the repo.

—

If you want, I can also:
- Produce a human-readable **step-by-step job plan** for the GitHub Actions workflow (without code), or  
- Generate a **sample run** (mock data) showing the exact Telegram Markdown output for a list of repos.

Reply `JobPlan` or `SampleRun` to choose. 