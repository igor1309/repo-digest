# scripts/generate_digest.py
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests

# --- Constants ---
API_URL = "https://api.github.com"
ISSUES_PER_REPO_LIMIT = 10
TITLE_WORD_CLAMP = 18

def escape_markdown_v2(text):
    """Escapes text for Telegram's MarkdownV2 parser."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))

def clamp_title(title):
    words = title.split()
    if len(words) > TITLE_WORD_CLAMP:
        return " ".join(words[:TITLE_WORD_CLAMP]) + "…"
    return title

NOTIFY_SCRIPT = Path(__file__).resolve().parent / "ci" / "notify_telegram.sh"

def send_telegram_message(token, chat_id, text, parse_mode="MarkdownV2"):
    """Sends a message to a Telegram chat via ci-shared transport."""
    env = {**os.environ, "TELEGRAM_DISABLE_PREVIEW": "true"}
    if parse_mode and parse_mode != "None":
        env["TELEGRAM_PARSE_MODE"] = parse_mode
    subprocess.run(
        [str(NOTIFY_SCRIPT), token, chat_id, text],
        check=True,
        env=env,
    )

def fetch_repo_data(repo_slug, token):
    """Fetches issue data for a single repository."""
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    repo_details_url = f"https://api.github.com/repos/{repo_slug}"
    try:
        repo_response = requests.get(repo_details_url, headers=headers, timeout=10)
        repo_response.raise_for_status()
        total_open_issues = repo_response.json().get("open_issues_count", 0)
    except requests.exceptions.RequestException as e:
        raise Exception(f"GitHub API Error for {repo_slug} (details): {e}")

    if total_open_issues == 0:
        return [], 0

    issues_url = f"https://api.github.com/repos/{repo_slug}/issues"
    params = {"state": "open", "sort": "created", "direction": "desc", "per_page": ISSUES_PER_REPO_LIMIT}
    try:
        issues_response = requests.get(issues_url, headers=headers, params=params, timeout=10)
        issues_response.raise_for_status()
        return issues_response.json(), total_open_issues
    except requests.exceptions.RequestException as e:
        raise Exception(f"GitHub API Error for {repo_slug} (issues): {e}")

def generate_report_text():
    """
    Fetches all data and builds the final, formatted report string.
    """
    gh_token = os.environ.get("GH_PAT")
    try:
        with open("repos.txt", "r") as f:
            repos = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        raise Exception("repos.txt not found.")

    if not repos:
        return "No repositories configured in repos\\.txt\\."

    # --- START OF SURGICAL CHANGE ---
    
    # Stage 1: Sort repositories into two lists
    repos_with_issues_parts = []
    repos_without_issues = []

    for repo_slug in repos:
        issues, total_open_count = fetch_repo_data(repo_slug, gh_token)
        actual_issues = [issue for issue in issues if 'pull_request' not in issue]

        if total_open_count == 0 or not actual_issues:
            repos_without_issues.append(repo_slug)
        else:
            # Build the multi-line string block for this repo
            repo_name = repo_slug.split('/')[-1]
            escaped_repo_name = escape_markdown_v2(repo_name)
            
            single_repo_parts = [f"\n*{escaped_repo_name}*"]
            for i, issue in enumerate(actual_issues):
                clamped_title = clamp_title(issue['title'])
                issue_num = issue['number']
                created_at = datetime.fromisoformat(issue['created_at'].replace("Z", "+00:00"))
                date_str = created_at.strftime("%Y-%m-%d")
                url = issue['html_url']
                link_text = f"#{issue_num} — {date_str} — {clamped_title}"
                escaped_link_text = escape_markdown_v2(link_text)
                single_repo_parts.append(f"{i + 1}\\. [{escaped_link_text}]({url})")

            if total_open_count > len(actual_issues):
                more_count = total_open_count - len(actual_issues)
                single_repo_parts.append(f"\nand {more_count} more issues")
            
            repos_with_issues_parts.append("  \n".join(single_repo_parts))

    # Stage 2: Assemble the final message from the sorted parts
    today = datetime.utcnow().strftime("%a, %Y-%m-%d")
    message_parts = [f"*Weekend issues report — {escape_markdown_v2(today)}*"]
    
    # Add the sections for repos that have issues
    message_parts.extend(repos_with_issues_parts)

    # Add the "No issues" section if there are any such repos
    if repos_without_issues:
        message_parts.append("\n*No issues*")
        for repo_slug in repos_without_issues:
            repo_name = repo_slug.split('/')[-1]
            escaped_repo_name = escape_markdown_v2(repo_name)
            message_parts.append(f"\\- {escaped_repo_name}")
            
    # --- END OF SURGICAL CHANGE ---
            
    return "  \n".join(message_parts)

def main():
    """
    Main execution block: generates the report and sends it to Telegram.
    Includes error handling to send a failure notification.
    """
    telegram_token = os.environ.get("TELEGRAM_TOKEN")
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not all([os.environ.get("GH_PAT"), telegram_token, telegram_chat_id]):
        sys.exit("Error: One or more required secrets are not set.")

    try:
        final_message = generate_report_text()
        print("--- Sending final message to Telegram ---")
        send_telegram_message(telegram_token, telegram_chat_id, final_message)

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        failure_message = f"Weekend issues report — FAILED: {e}"
        send_telegram_message(telegram_token, telegram_chat_id, failure_message, parse_mode="None")
        sys.exit(1)

if __name__ == "__main__":
    main()