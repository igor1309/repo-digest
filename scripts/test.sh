#!/usr/bin/env bash
set -euo pipefail

node --test scripts/weekly_releases_period.test.mjs scripts/weekly_releases_telegram.test.mjs
