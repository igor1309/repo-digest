# scripts/generate_digest.py
import os
import sys
import requests
import time
from datetime import datetime

# --- Constants as per SPEC ---
API_URL = "https://api.github.com"
ISSUES_PER_REPO_LIMIT = 10
API_PAGE_SIZE = ISSUES_PER_REPO_LIMIT + 1
TITLE_WORD_CLAMP = 18

# --- Helper function for sanitizing titles ---
def sanitize_title(title):
    """
    Sanitizes issue titles for Telegram's legacy Markdown by escaping
    special characters.
    """
    # Characters that have special meaning in Telegram's legacy Markdown
    # We will escape these characters with a backslash.
    # Note: We don't escape '#' as we use it for issue numbers.
    # We don't escape '@' as we use it for usernames.
    # We remove backticks as they are problematic even when escaped.
    
    escape_chars = r'_*[]()~`>#+-=|{}.!'

    # First, remove backticks completely as they are tricky.
    sanitized_title = title.replace('`', '')
    
    # Now, escape the other special characters
    for char in escape_chars:
        if char in sanitized_title:
             # The character `\` is the escape character, so it needs to be escaped itself in the replacement string.
            sanitized_title = sanitized_title.replace(char, '\\' + char)
            
    return sanitized_title

# --- Helper function for clamping titles ---
def clamp_title(title):
    """
    Truncates a title to a specific number of words.
    """
    words = title.split()
    if len(words) > TITLE_WORD_CLAMP:
        return " ".join(words[:TITLE_WORD_CLAMP]) + "…"
    return title

# --- Helper function to send a message to Telegram ---
def send_telegram_message(token, chat_id, text):
    """
    Sends a message to a Telegram chat using the bot API.
    Uses legacy 'Markdown' parse mode.
    """
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown", # Legacy Markdown as per SPEC
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("Telegram message sent successfully.")
    except requests.exceptions.RequestException as e:
        # Print the error to the GitHub Actions log for debugging
        print(f"Error sending Telegram message: {e}")
        # Also print the response body if available, as it contains useful info
        if e.response is not None:
            print(f"Telegram API response: {e.response.text}")
        sys.exit(1) # Exit with failure if we can't notify the user

# --- Updated GitHub API fetching function ---
def fetch_repo_data(repo_slug, token):
    """
    Fetches open issues and the total count of open issues for a repository.
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    # First, get the repo details to find the accurate 'open_issues_count'
    repo_details_url = f"{API_URL}/repos/{repo_slug}"
    try:
        repo_response = requests.get(repo_details_url, headers=headers, timeout=10)
        repo_response.raise_for_status()
        total_open_issues = repo_response.json().get("open_issues_count", 0)
    except requests.exceptions.RequestException as e:
        error_message = f"API Error getting repo details for {repo_slug}: {e}"
        return None, 0, error_message

    if total_open_issues == 0:
        return [], 0, None

    # Second, get the list of newest issues
    issues_url = f"{API_URL}/repos/{repo_slug}/issues"
    params = {
        "state": "open",
        "sort": "created",
        "direction": "desc",
        "per_page": ISSUES_PER_REPO_LIMIT, # Only fetch the amount we will display
    }
    try:
        issues_response = requests.get(issues_url, headers=headers, params=params, timeout=10)
        issues_response.raise_for_status()
        issues = issues_response.json()
        return issues, total_open_issues, None
    except requests.exceptions.RequestException as e:
        error_message = f"API Error fetching issues for {repo_slug}: {e}"
        return None, 0, error_message

def main():
    gh_token = os.environ.get("GH_PAT")
    telegram_token = os.environ.get("TELEGRAM_TOKEN")
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not all([gh_token, telegram_token, telegram_chat_id]):
        print("Error: Required secrets are not set.")
        sys.exit(1)

    try:
        with open("repos.txt", "r") as f:
            repos = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Error: repos.txt not found.")
        sys.exit(1)

    if not repos:
        print("Warning: repos.txt is empty.")
        return

    # --- Build the Markdown message ---
    # Get current date in UTC and format it for the title
    today = datetime.utcnow().strftime("%a, %Y-%m-%d")
    message_parts = [f"*Weekend issues report — {today}*"]

    for repo_slug in repos:
        print(f"Processing {repo_slug}...")
        issues, total_open_count, error = fetch_repo_data(repo_slug, gh_token)

        message_parts.append(f"\n*## {repo_slug}*")

        if error:
            message_parts.append(f"Could not fetch issues: `{error}`")
            continue

        if not issues:
            message_parts.append("No open issues.")
            continue

        for i, issue in enumerate(issues):
            # Skip pull requests
            if 'pull_request' in issue:
                continue
            
            # Sanitize, clamp, and format data as per SPEC
            title = sanitize_title(issue['title'])
            clamped_title = clamp_title(title)
            issue_num = issue['number']
            # Parse date string and format to YYYY-MM-DD
            created_at = datetime.fromisoformat(issue['created_at'].replace("Z", "+00:00"))
            date_str = created_at.strftime("%Y-%m-%d")
            author = issue['user']['login']
            url = issue['html_url']

            message_parts.append(
                f"{i + 1}. {clamped_title} — #{issue_num} — {date_str} — @{author} — {url}"
            )

        if total_open_count > ISSUES_PER_REPO_LIMIT:
            more_count = total_open_count - ISSUES_PER_REPO_LIMIT
            message_parts.append(f"\nand {more_count} more issues")

    # Join all parts into a single message string
    final_message = "\n".join(message_parts)
    
    print("\n--- Generated Message ---")
    print(final_message)
    print("-------------------------\n")

    # Send the final message to Telegram
    send_telegram_message(telegram_token, telegram_chat_id, final_message)

if __name__ == "__main__":
    main()