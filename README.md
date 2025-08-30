# Weekend Issues Digest

![bot_icon](bot_icon.JPG)

**Weekend snapshot of open issues from your private GitHub repositories delivered to your Telegram bot.**

This is a simple personal automation that runs on a schedule to fetch open issues from your GitHub repositories and post a structured report to a Telegram chat. The report groups repositories with open issues, lists the newest issues for each, and summarizes the rest. Repositories with no open issues are listed separately.

## Setup

To run this automation, you will need to configure:

- A list of your target GitHub repositories.
- Credentials for the GitHub API and a Telegram bot.
- A scheduled environment to execute the script.

For all implementation details, message formats, and specific configuration values, please refer to **[SPEC.md](docs/SPEC.md)**, which is the single source of truth.
