# scripts/generate_digest.py
import os
import sys

def main():
    """
    Main function to load secrets, read repos, and eventually generate the digest.
    """
    # Load secrets from environment variables
    gh_token = os.environ.get("GH_PAT")
    telegram_token = os.environ.get("TELEGRAM_TOKEN")
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    # --- Verification Step ---
    # Ensure all required secrets are present.
    if not all([gh_token, telegram_token, telegram_chat_id]):
        print("Error: One or more required secrets (GH_PAT, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID) are not set.")
        sys.exit(1) # Exit with a failure code

    print("Secrets loaded successfully.")

    # --- Read Repositories ---
    try:
        with open("repos.txt", "r") as f:
            repos = [line.strip() for line in f if line.strip()]
        
        if not repos:
            print("Warning: repos.txt is empty or contains no valid repository lines.")
        
        print("Repositories to process:")
        for repo in repos:
            print(f"- {repo}")

    except FileNotFoundError:
        print("Error: repos.txt not found at the repository root.")
        sys.exit(1)

if __name__ == "__main__":
    main()
