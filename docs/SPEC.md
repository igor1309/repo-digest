# SPEC — Weekend Issues Digest

This SPEC is the authoritative implementation document for **Weekend Issues Digest**.
Keep this file as the single source of truth for behavior, edge cases, message template, secrets, and testing.

---

## Task
Produce an automated **Weekend Issues Report** sent to a Telegram bot on **Saturday and Sunday at 07:15 MSK** (04:15 UTC). The report lists **all open issues** for a predetermined set of **private** GitHub repositories. The set of repositories is editable without changing workflow code via `repos.txt`.

---

## Inputs & Artifacts
- `repos.txt` (required): plain text file at the repo root. Each non-empty line is an `owner/repo` identifier. Editable via GitHub UI.
  ```
  youruser/project-one
  youruser/project-two
  ```

- Secrets (GitHub repository secrets recommended):
  - `GH_PAT` — Personal Access Token (minimum read access to private repos; `repo` scope).  
  - `TELEGRAM_TOKEN` — Telegram bot token.  
  - `TELEGRAM_CHAT_ID` — numeric chat or channel id.

- Workflow: stored in this repo (automation repo). Reads `repos.txt` at runtime.

---

## Selection & Sorting Rules (exact)
- **Include:** All issues with `state=open` for each listed repo (explicit: open issues only).  
  - If you meant differently (e.g., include closed), edit SPEC accordingly before implementation.
- **Sort:** by `created_at` descending (newest created first).
- **Display limit:** show up to **10** issues per repo. To detect overflow, request up to **11** items or use API pagination/headers. If total open > 10, append: `and N more issues` where `N = total_open - 10`.
- **Title clamp:** truncate to **18 words** (split on whitespace). If truncated, append `…`. Word count, not characters.
- **Date format:** `YYYY-MM-DD` (use the issue's `created_at` converted to UTC then formatted).
- **Author:** include the issue author username prefixed with `@`.
- **Link:** include full GitHub issue URL.

---

## Message format (Telegram legacy Markdown)
- Use **legacy Markdown** (non-V2).
- Single-run message: build a Markdown document containing repo sections in the same order as `repos.txt`.
- Template:
```
# Weekend issues report — Sat, 2025-09-06

## owner/repo-1
1. Issue title (clamped to 18 words) — #123 — 2025-09-05 — @author — https://github.com/owner/repo-1/issues/123
2. Another issue title … — #122 — 2025-09-04 — @someone — https://github.com/owner/repo-1/issues/122

and 7 more issues

## owner/repo-2
No open issues.
```
- If a repo has 0 open issues: show `No open issues.` under that repo heading.
- Keep each Telegram message ≤ **4096 characters**. If the composed report exceeds that:
  - Split into additional messages by whole repo sections; avoid splitting a repo section across messages unless a single section itself exceeds the limit.
  - If a single repo section exceeds 4096 chars, split between items within that section.

---

## Sanitization & Markdown safety (legacy Markdown rules)
- Legacy Markdown accepts `*`, `_`, and backticks; however titles containing unmatched brackets or code ticks can break rendering.
- Minimal sanitization required:
  - Remove backticks `` ` `` from titles.
  - Remove or neutralize stray unmatched `[` `]` `(` `)` characters that could break link parsing.
  - Do not attempt full MarkdownV2 escaping; keep sanitization conservative to preserve readability.
- Links and explicit `#<number>` tokens are safe to include.

---

## API usage & pagination notes
- Use GitHub Issues API per repo: request open issues sorted by `created` (descending). Use `per_page=11` to detect overflow or query total counts via appropriate endpoints/headers.
- For private repos: authenticate with `GH_PAT` having necessary read scopes.
- Respect API rate limits — personal use is unlikely to hit limits, but implement simple backoff on 429/abuse responses.

---

## Error handling & retries
- On transient errors (network, 5xx, rate-limit): retry up to 2 times with short backoff (e.g., exponential: 1s → 3s).
- On fatal or repeated errors: send a short Telegram message to the configured chat:
```
Weekend issues report — FAILED: <short error summary>
```
- Do not include tokens, authentication data, or raw API responses in Telegram messages.
- Preserve workflow logs for debugging and optionally create an issue in this repo on persistent failure.

---

## Testing checklist
1. Populate `repos.txt` with 2–3 repos (mix of volumes). Include issue titles with special characters for sanitization testing.
2. Set secrets (`GH_PAT`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`) in repo settings.
3. Provide a manual trigger (`workflow_dispatch`) and run a manual job.
4. Verify Telegram output:
   - Repo sections appear in `repos.txt` order.
   - Issues sorted by creation date descending.
   - Titles clamped to 18 words and show `…` if truncated.
   - `and N more issues` appears when there are >10 open issues.
   - Messages do not exceed 4096 chars; splitting behavior is correct.
5. Test error path by using invalid `GH_PAT` and confirm a short failure message delivered.

---

## Deployment checklist (for implementer)
1. Ensure `repos.txt` exists at repo root and contains `owner/repo` lines.
2. Add required secrets to repository settings.
3. Create scheduled workflow (recommended GitHub Actions) that:
   - Runs at 04:15 UTC on Saturday and Sunday and supports manual dispatch.
   - Reads `repos.txt`.
   - For each repo, fetches open issues sorted by created desc.
   - Builds Markdown message(s) per Message format rules and sanitization guidelines.
   - Posts to Telegram using `TELEGRAM_TOKEN`/`TELEGRAM_CHAT_ID`.
   - Retries transient errors; posts concise failure on fatal errors.
4. Test and iterate on sanitization if Markdown rendering issues occur.

---

## Maintenance & notes
- Rotate `GH_PAT` periodically.
- Keep `repos.txt` under version control for auditability.
- If you need per-repo metadata later, consider migrating to a structured `repos.yaml` and update SPEC accordingly.
- This SPEC is the single source of truth for behavior — update it if you change message rules, limits, or schedule.

---
