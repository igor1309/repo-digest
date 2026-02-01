---
date: 2026-02-01
model: gpt-5.2
description: "Authoritative behavior and workflow rules for the digest automation."
---

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

## Repo list check

The workflow runs `scripts/diff-repos-txt-vs-live.sh` (since `2025-01-01`) and sends a Telegram MarkdownV2 message listing any missing repos. The digest still runs regardless of the check result.

---

## Selection & Sorting Rules (exact)

- **Include:** All issues with `state=open` for each listed repo (explicit: open issues only).
- **Sort:** by `created_at` descending (newest created first).
- **Display limit:** show up to **10** issues per repo. If total open > 10, append: `and N more issues` where `N = total_open - 10`.
- **Title clamp:** truncate to **18 words** (split on whitespace). If truncated, append `…`. Word count, not characters.
- **Date format:** `YYYY-MM-DD` (use the issue's `created_at` converted to UTC then formatted).
- **Link:** include full GitHub issue URL as a clickable link.

---

## Message format (Telegram MarkdownV2)

- Use **MarkdownV2**.
- The report is structured into two main groups: repositories with open issues are listed first, followed by a summary section for repositories with no open issues.
- Within each group, repositories appear in the same order as they are listed in `repos.txt`.
- Template:

```
*Weekend issues report — Sat, 2025-09-06*

*project-one*
1\. [#123 — 2025-09-05 — Issue title clamped to 18 words](https://github.com/owner/repo-1/issues/123)

and 7 more issues

*project-three*
1\. [#45 — 2025-09-06 — A brand new issue](https://github.com/owner/repo-3/issues/45)

*No issues*
- project-two
- project-four
```

- **Message length:** The report is generated as a single message. In the rare case it exceeds Telegram's character limit (4096 chars), it may be truncated. No complex message splitting logic will be implemented.

---

## Sanitization & Markdown safety (MarkdownV2 Escaping)

- MarkdownV2 requires escaping of special characters (`_`, `*`, `[`, `]`, `(`, `)`, `~`, ` \``,  `>`, `#`, `+`, `-`, `=`, `|`, `{`, `}`, `.`, `!`).
- All dynamic content (repo names, issue titles, dates) included in the message must be properly escaped with a preceding backslash `\` to render correctly.

---

## API usage & pagination notes

- To get an accurate count for the `and N more issues` message, first query the repository details endpoint (`/repos/{owner}/{repo}`) to get the exact `open_issues_count`. Then, fetch the issues list with `per_page=10`.
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
   - Repos with issues appear first, then a "No issues" section.
   - Order within each section is preserved from `repos.txt`.
   - Issues sorted by creation date descending.
   - Titles clamped to 18 words and show `…` if truncated.
   - `and N more issues` appears when there are >10 open issues.
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
