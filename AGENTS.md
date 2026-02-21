---
date: 2026-02-21
model: gpt-5.3-codex
description: "Repo-specific agent rules for test execution and log maintenance."
---

# Repo Agent Notes

## Tests Before Commit

- Run tests before every commit using:
  - `./scripts/run_silent.sh "tests" ./scripts/test.sh`
- Do not bypass the wrapper for routine verification.
- Do not commit when this command fails.

## `docs/log.md` Requirements

- Update `docs/log.md` for each meaningful change set before pushing.
- Keep entries concise and outcome-focused.
- Keep newest outcomes first inside the current date section.
- Do not copy commit messages verbatim.
