# main.py
import os
import sys

def main():
    """
    Main function to read inputs and secrets.
    """
    # --- 1. Read Secrets from Environment Variables ---
    # The workflow passes secrets as environment variables for security.
    gh_token = os.environ.get("GH_PAT")
    telegram_token = os.environ.get("TELEGRAM_TOKEN")
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    print("--- Secrets ---")
    print(f"GH_PAT: {'Loaded' if gh_token else 'NOT FOUND'}")
    print(f"TELEGRAM_TOKEN: {'Loaded' if telegram_token else 'NOT FOUND'}")
    print(f"TELEGRAM_CHAT_ID: {'Loaded' if telegram_chat_id else 'NOT FOUND'}")

    if not all([gh_token, telegram_token, telegram_chat_id]):
        print("\nError: One or more required secrets are missing.")
        # sys.exit(1) # We'll enable this later

    # --- 2. Read Repositories from repos.txt ---
    try:
        with open('repos.txt', 'r') as f:
            # Read lines, strip whitespace, and filter out empty lines
            repos = [line.strip() for line in f if line.strip()]
        
        print("\n--- Repositories to process ---")
        if repos:
            for repo in repos:
                print(f"- {repo}")
        else:
            print("repos.txt is empty or not found.")

    except FileNotFoundError:
        print("\nError: repos.txt not found.")
        sys.exit(1)


if __name__ == "__main__":
    main()
