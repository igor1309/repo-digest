# scripts/generate_digest.py
import os
import sys
import requests
import time

# --- Constants as per SPEC ---
API_URL = "https://api.github.com"
ISSUES_PER_REPO_LIMIT = 10
# Request 11 to detect if there are more than 10 issues
API_PAGE_SIZE = ISSUES_PER_REPO_LIMIT + 1

def fetch_issues(repo_slug, token):
    """
    Fetches open issues for a single repository.
    repo_slug: string, e.g., "owner/repo"
    token: string, GitHub PAT
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    # API params based on SPEC: open state, sorted by creation date descending
    params = {
        "state": "open",
        "sort": "created",
        "direction": "desc",
        "per_page": API_PAGE_SIZE,
    }
    
    url = f"{API_URL}/repos/{repo_slug}/issues"
    print(f"Fetching issues for {repo_slug}...")

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()

        issues = response.json()
        # The 'total_count' for issues is not available directly on this endpoint.
        # We determine if there are more issues by checking if we received 11 items.
        # Note: Pull Requests are also returned by this API endpoint. The SPEC doesn't
        # exclude them, so we'll include them.
        
        has_more = len(issues) > ISSUES_PER_REPO_LIMIT
        
        # We don't have the *exact* total count, but we can get it from another API call or search.
        # For now, let's keep it simple as per SPEC's guidance. The number of 'more'
        # can be calculated later if we get the total count. For now, we just know *if* there's more.
        
        # Trim the list to the display limit
        display_issues = issues[:ISSUES_PER_REPO_LIMIT]
        
        return display_issues, has_more, None # No error

    except requests.exceptions.RequestException as e:
        error_message = f"API Error for {repo_slug}: {e}"
        print(error_message)
        return [], False, error_message


def main():
    """
    Main function to load secrets, read repos, and generate the digest.
    """
    # Load secrets from environment variables
    gh_token = os.environ.get("GH_PAT")
    telegram_token = os.environ.get("TELEGRAM_TOKEN")
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not all([gh_token, telegram_token, telegram_chat_id]):
        print("Error: Required secrets are not set.")
        sys.exit(1)

    print("Secrets loaded successfully.")

    try:
        with open("repos.txt", "r") as f:
            repos = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Error: repos.txt not found.")
        sys.exit(1)

    if not repos:
        print("Warning: repos.txt is empty.")
        return # Exit gracefully

    # --- Process each repository ---
    for repo in repos:
        issues, has_more, error = fetch_issues(repo, gh_token)

        if error:
            # For now, we just print the error and continue.
            # In a later step, we'll implement the full error handling logic.
            continue
        
        print(f"\n--- Results for {repo} ---")
        if not issues:
            print("No open issues found.")
        else:
            for issue in issues:
                print(f"  - #{issue['number']}: {issue['title']}")
        
        if has_more:
            print(f"  ... and more issues exist beyond the first {ISSUES_PER_REPO_LIMIT}.")
        print("-------------------------\n")


if __name__ == "__main__":
    main()