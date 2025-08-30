# Weekend Issues Digest

**Tagline:** Weekend snapshot of open issues from your private GitHub repositories delivered to your Telegram bot.

**Purpose:** Simple personal automation. Runs Saturdays & Sundays at **07:15 MSK** and posts a structured Markdown report to a Telegram chat.

**Quick start (3 steps)**
1. Add `repos.txt` (root of this repo) — one `owner/repo` per line.  
2. Add secrets in repository settings → Secrets: `GH_PAT`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`.  
3. Add and enable the scheduled workflow (recommended: GitHub Actions) with a manual `workflow_dispatch` trigger. Schedule: **04:15 UTC** on Sat & Sun.

For full authoritative behavior, message format, edge-cases and testing instructions see **SPEC.md** (single source of truth).
