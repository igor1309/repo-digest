# scripts/generate_digest.py
import os
import sys
import requests
import re
from datetime import datetime

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

def send_telegram_message(token, chat_id, text):
    """Sends a message to a Telegram chat using MarkdownV2."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = { "chat_id": chat_id, "text": text, "parse_mode": "MarkdownV2", "disable_web_page_preview": True }
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        print("Telegram message sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message: {e}", file=sys.stderr)
        if e.response is not None:
            print(f"Telegram API response: {e.response.text}", file=sys.stderr)
        sys.exit(1)

def fetch_repo_data(repo_slug, token):
    """Fetches issue data for a single repository."""
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    repo_details_url = f"{API_URL}/repos/{repo_slug}"
    try:
        repo_response = requests.get(repo_details_url, headers=headers, timeout=10)
        repo_response.raise_for_status()
        total_open_issues = repo_response.json().get("open_issues_count", 0)
    except requests.exceptions.RequestException as e:
        raise Exception(f"GitHub API Error for {repo_slug} (details): {e}")

    if total_open_issues == 0:
        return [], 0

    issues_url = f"{API_URL}/repos/{repo_slug}/issues"
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
    This function has no side effects (like sending messages).
    """
    gh_token = os.environ.get("GH_PAT")
    try:
        with open("repos.txt", "r") as f:
            repos = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        raise Exception("repos.txt not found.")

    if not repos:
        return "No repositories configured in repos\\.txt\\."

    today = datetime.utcnow().strftime("%a, %Y-%m-%d")
    message_parts = [f"*Weekend issues report — {escape_markdown_v2(today)}*"]

    for repo_slug in repos:
        message_parts.append(f"\n*{escape_markdown_v2(repo_slug)}*")
        
        issues, total_open_count = fetch_repo_data(repo_slug, gh_token)
        actual_issues = [issue for issue in issues if 'pull_request' not in issue]

        if total_open_count == 0 or not actual_issues:
            message_parts.append("No open issues\\.")
            continue

        for i, issue in enumerate(actual_issues):
            clamped_title = clamp_title(issue['title'])
            issue_num = issue['number']
            created_at = datetime.fromisoformat(issue['created_at'].replace("Z", "+00:00"))
            date_str = created_at.strftime("%Y-%m-%d")
            url = issue['html_url']
            
            link_text = f"#{issue_num} — {date_str} — {clamped_title}"
            escaped_link_text = escape_markdown_v2(link_text)
            message_parts.append(f"{i + 1}\\. [{escaped_link_text}]({url})")

        if total_open_count > len(actual_issues):
            more_count = total_open_count - len(actual_issues)
            message_parts.append(f"\nand {more_count} more issues")
            
    return "\n".join(message_parts)

def main():
    """
    This main function is for TESTING ONLY.
    It generates the report and prints it to the console.
    It DOES NOT send a message to Telegram.
    """
    if not all([os.environ.get("GH_PAT"), os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")]):
        sys.exit("Error: Required secrets are not set.")

    try:
        final_message = generate_report_text()
        print("--- START OF GENERATED MESSAGE ---")
        print(final_message)
        print("--- END OF GENERATED MESSAGE ---")
    except Exception as e:
        print(f"An error occurred during message generation: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()