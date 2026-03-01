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
TELEGRAM_MAX_LENGTH = 4000
MESSAGE_SEPARATOR = "  \n"

def escape_markdown_v2(text):
    """Escapes text for Telegram's MarkdownV2 parser."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))

def clamp_title(title):
    words = title.split()
    if len(words) > TITLE_WORD_CLAMP:
        return " ".join(words[:TITLE_WORD_CLAMP]) + "…"
    return title

def send_telegram_message(token, chat_id, text, parse_mode="MarkdownV2"):
    """Sends a message to a Telegram chat."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = { "chat_id": chat_id, "text": text, "parse_mode": parse_mode, "disable_web_page_preview": True }
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        print("Telegram message sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message: {e}", file=sys.stderr)
        if e.response is not None:
            print(f"Telegram API response: {e.response.text}", file=sys.stderr)
        # We let the main function handle the exit
        raise

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

def generate_report_parts():
    """
    Fetches all data and builds the report header and content sections.
    Returns (header, content_sections) where content_sections is a list of strings.
    """
    gh_token = os.environ.get("GH_PAT")
    try:
        with open("repos.txt", "r") as f:
            repos = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        raise Exception("repos.txt not found.")

    today = datetime.utcnow().strftime("%a, %Y-%m-%d")
    header = f"*Weekend issues report — {escape_markdown_v2(today)}*"

    if not repos:
        return header, ["No repositories configured in repos\\.txt\\."]

    repos_with_issues_parts = []
    repos_without_issues = []

    for repo_slug in repos:
        issues, total_open_count = fetch_repo_data(repo_slug, gh_token)
        actual_issues = [issue for issue in issues if 'pull_request' not in issue]

        if total_open_count == 0 or not actual_issues:
            repos_without_issues.append(repo_slug)
        else:
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

            repos_with_issues_parts.append(MESSAGE_SEPARATOR.join(single_repo_parts))

    content_sections = list(repos_with_issues_parts)

    if repos_without_issues:
        no_issues_lines = ["\n*No issues*"]
        for repo_slug in repos_without_issues:
            repo_name = repo_slug.split('/')[-1]
            escaped_repo_name = escape_markdown_v2(repo_name)
            no_issues_lines.append(f"\\- {escaped_repo_name}")
        content_sections.append(MESSAGE_SEPARATOR.join(no_issues_lines))

    return header, content_sections


def chunk_message(header, content_sections, max_length=TELEGRAM_MAX_LENGTH):
    """Group content sections into messages that fit within Telegram's character limit."""
    if not content_sections:
        return [header]

    cont_header = header[:-1] + " \\(cont\\.\\)*"
    chunks = []
    current = header
    has_content = False

    for section in content_sections:
        candidate = current + MESSAGE_SEPARATOR + section
        if len(candidate) > max_length and has_content:
            chunks.append(current)
            current = cont_header
            has_content = False
            candidate = current + MESSAGE_SEPARATOR + section

        current = candidate
        has_content = True

    chunks.append(current)
    return chunks

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
        header, content_sections = generate_report_parts()
        chunks = chunk_message(header, content_sections)
        print(f"--- Sending {len(chunks)} message(s) to Telegram ---")
        for chunk in chunks:
            send_telegram_message(telegram_token, telegram_chat_id, chunk)

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        failure_message = f"Weekend issues report — FAILED: {e}"
        send_telegram_message(telegram_token, telegram_chat_id, failure_message, parse_mode="None")
        sys.exit(1)

if __name__ == "__main__":
    main()