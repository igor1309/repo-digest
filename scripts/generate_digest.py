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

# --- NEW: MarkdownV2 Escaping Function ---
def escape_markdown_v2(text):
    """
    Escapes text for Telegram's MarkdownV2 parser.
    """
    # List of characters to escape
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    # Use re.sub to add a backslash before each special character
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

# --- Helper function for clamping titles ---
def clamp_title(title):
    words = title.split()
    if len(words) > TITLE_WORD_CLAMP:
        return " ".join(words[:TITLE_WORD_CLAMP]) + "…"
    return title

# --- Helper function to send a message to Telegram ---
def send_telegram_message(token, chat_id, text):
    """
    Sends a message to a Telegram chat using the bot API with MarkdownV2.
    """
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "MarkdownV2", # CORRECTED: Using the robust V2 parser
        "disable_web_page_preview": True,
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("Telegram message sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message: {e}")
        if e.response is not None:
            print(f"Telegram API response: {e.response.text}")
        sys.exit(1)

# --- GitHub API fetching function (no changes needed here) ---
def fetch_repo_data(repo_slug, token):
    headers = { "Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    repo_details_url = f"{API_URL}/repos/{repo_slug}"
    try:
        repo_response = requests.get(repo_details_url, headers=headers, timeout=10)
        repo_response.raise_for_status()
        total_open_issues = repo_response.json().get("open_issues_count", 0)
    except requests.exceptions.RequestException as e:
        return None, 0, f"API Error: {e}"

    if total_open_issues == 0:
        return [], 0, None

    issues_url = f"{API_URL}/repos/{repo_slug}/issues"
    params = {"state": "open", "sort": "created", "direction": "desc", "per_page": ISSUES_PER_REPO_LIMIT}
    try:
        issues_response = requests.get(issues_url, headers=headers, params=params, timeout=10)
        issues_response.raise_for_status()
        return issues_response.json(), total_open_issues, None
    except requests.exceptions.RequestException as e:
        return None, 0, f"API Error: {e}"

def main():
    gh_token = os.environ.get("GH_PAT")
    telegram_token = os.environ.get("TELEGRAM_TOKEN")
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not all([gh_token, telegram_token, telegram_chat_id]):
        sys.exit("Error: Required secrets are not set.")

    try:
        with open("repos.txt", "r") as f:
            repos = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        sys.exit("Error: repos.txt not found.")

    if not repos:
        print("Warning: repos.txt is empty.")
        return

    today = datetime.utcnow().strftime("%a, %Y-%m-%d")
    # We will escape the date string just in case
    message_parts = [f"*Weekend issues report — {escape_markdown_v2(today)}*"]

    for repo_slug in repos:
        print(f"Processing {repo_slug}...")
        issues, total_open_count, error = fetch_repo_data(repo_slug, gh_token)

        # Escape the repo slug before wrapping it in bold markers
        message_parts.append(f"\n*{escape_markdown_v2(repo_slug)}*")

        if error:
            message_parts.append(f"`{escape_markdown_v2(error)}`")
            continue

        if total_open_count == 0:
            message_parts.append("No open issues.")
            continue
        
        actual_issues = [issue for issue in issues if 'pull_request' not in issue]
        if not actual_issues:
            message_parts.append("No open issues")
            continue


        for i, issue in enumerate(actual_issues):
            clamped_title = clamp_title(issue['title'])
            issue_num = issue['number']
            created_at = datetime.fromisoformat(issue['created_at'].replace("Z", "+00:00"))
            date_str = created_at.strftime("%Y-%m-%d")
            url = issue['html_url']

            # Create the link text, THEN escape it fully.
            link_text = f"#{issue_num} — {date_str} — {clamped_title}"
            escaped_link_text = escape_markdown_v2(link_text)
            
            # The list number period also needs escaping.
            message_parts.append(f"{i + 1}\\. [{escaped_link_text}]({url})")

        if total_open_count > len(actual_issues):
            more_count = total_open_count - len(actual_issues)
            # Escape the text here too for consistency
            message_parts.append(f"\nand {more_count} more issues")

    final_message = "\n".join(message_parts)
    
    print("\n--- Generated Message ---")
    print(final_message)
    print("-------------------------\n")

    send_telegram_message(telegram_token, telegram_chat_id, final_message)

if __name__ == "__main__":
    main()