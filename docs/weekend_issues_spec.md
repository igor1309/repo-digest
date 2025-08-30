# Task
Produce an automated **Weekend Issues Report** sent to a Telegram bot.  
Runs **Saturday and Sunday at 07:15 MSK** (04:15 UTC). The report lists **all open issues** for a predetermined set of private GitHub repositories. The repository list is editable without changing automation code.

# Scope
- Read `repos.txt` from the automation repository root (one `owner/repo` per line).  
- For each listed repo, fetch **all open issues**, sort by **created date descending**, and include up to **10** items. If more than 10 open issues exist, append `and N more issues`.  
- Compose a **single Markdown** message (Telegram legacy `Markdown`) structured by repo sections and post it to a configured Telegram chat via your bot.

# Requirements (explicit)
- Use legacy Telegram **Markdown** (not MarkdownV2).  
- Titles must be **clamped to 18 words** (words count; append `…` if truncated).  
- Each repo section: `## owner/repo` heading, then a numbered list or `No open issues.`  
- Each list item format:  
  `1. Issue title (clamped) — #<issue-number> — YYYY-MM-DD — @author — https://github.com/owner/repo/issues/<n>`
- Message size: keep each Telegram message ≤ **4096 characters**. If the full report exceeds that, split into multiple messages by repo sections, avoiding splitting a repo section unless necessary.

# Files & artifacts
- `repos.txt` (required): plain text file at repo root, one `owner/repo` per line. Editable via GitHub web UI. Keep under version control.
  ```
  youruser/project-one
  youruser/project-two
  ```
- Automation workflow stored in automation repo (separate). The workflow reads `repos.txt` at runtime.

# Secrets (store in GitHub Secrets)
- `GH_PAT` — Personal Access Token with minimum scope to read private repos (recommend `repo` read scope only).  
- `TELEGRAM_TOKEN` — Bot token (e.g., `1234:ABC...`).  
- `TELEGRAM_CHAT_ID` — Numeric chat id or channel id.

# Schedule
- Run at **04:15 UTC** on Saturday and Sunday (this equals **07:15 MSK**). Use the workflow scheduler (or cron equivalent if using a different runner).

# Data selection & sorting rules (exact)
- Include issues with `state=open`. (You explicitly asked to list **all issues — no filter**; here "all" refers to all open issues as earlier agreed. If you meant literally *every* issue including closed, change this.)  
- Sort results by `created_at` descending.  
- For each repo:
  - Request up to **11** items to detect whether more than 10 exist (10 for display + 1 to check overflow). Alternatively use the API's total count via pagination/headers.
  - Clamp title to 18 words; sanitize/remove Markdown-sensitive characters that could break rendering (minimal sanitization for legacy Markdown: remove backticks and unmatched brackets/parentheses).

# Message template (Telegram Markdown)
```
# Weekend issues report — Sat, 2025-09-06

## owner/repo-1
1. Issue title (clamped to 18 words) — #123 — 2025-09-05 — @author — https://github.com/owner/repo-1/issues/123
2. Another issue title … — #122 — 2025-09-04 — @someone — https://github.com/owner/repo-1/issues/122

and 7 more issues

## owner/repo-2
No open issues.

(Repeat repo sections in the same order as repos.txt)
```

# Error handling & retries
- Retries: on transient network/API errors retry a small number of times (e.g., 2 retries with short backoff).  
- Fatal error: send a short Telegram message `Weekend issues report — FAILED: <short error summary>`. Do not post raw tokens or sensitive data.  
- Logging: preserve workflow logs for debugging. Optionally create an issue in the automation repo on persistent failure.

# Edge cases & exact behavior
- If a title contains Markdown tokens (`*`, `_`, `[`, `]`, `(`, `)`, `` ` ``), minimally sanitize by removing problematic characters. Legacy Markdown is forgiving; do not use full MarkdownV2 escaping.  
- If a repo has exactly 0 open issues, show `No open issues.` under that repo.  
- If the full text for a single repo section alone exceeds 4096 chars (unlikely), then split that repo across multiple messages between items.  
- Keep per-message character count ≤ 4096.

# Testing checklist (manual)
1. Populate `repos.txt` with 2–3 repos containing a variety of issues (some with long titles and special chars).  
2. Add secrets to repo: `GH_PAT`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`.  
3. Provide a manual trigger option and run the workflow via manual dispatch.  
4. Verify the Telegram message(s): structure, per-repo sections, clamped titles, “and N more issues” when applicable.  
5. Test error path by temporarily using an invalid PAT and confirming a short failure message is delivered.

# Deployment checklist (no code)
1. Add `repos.txt` to automation repo root.  
2. Add required secrets to repository settings → Secrets.  
3. Add a workflow that:
   - Runs at 04:15 UTC on Sat and Sun and supports manual dispatch.  
   - Reads `repos.txt` and for each non-empty trimmed line requests open issues sorted by created date desc.  
   - Builds Markdown message(s) following the template and message size rules.  
   - Posts to Telegram using `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID`.  
   - On fatal errors, posts a concise failure message.  
4. Run manual tests and adjust sanitization if Markdown rendering breaks.

# Maintenance notes
- Rotate `GH_PAT` regularly.  
- Keep `repos.txt` under version control for auditability.  
- If you add per-repo metadata later (display name, custom section title), consider migrating to `repos.yaml`.

# Example (single small repo sample output)
```
# Weekend issues report — Sun, 2025-09-07

## youruser/example-repo
1. Fix crash when opening file with empty metadata — #42 — 2025-09-07 — @alice — https://github.com/youruser/example-repo/issues/42
2. Improve documentation for import CLI — #41 — 2025-09-05 — @bob — https://github.com/youruser/example-repo/issues/41
```

# Final notes
- This spec is intentionally minimal and focused on reliability and editability (uses `repos.txt`).  
- If you want the exact step-by-step GitHub Actions job plan (human-readable steps without code), say `A`. If you want a sample run using mock data expanded into the exact final message format, say `B`.  
- The automation assumes "all issues" means **all open issues**. If you meant different, state the exact change now.

