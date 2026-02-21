#!/usr/bin/env node

/**
 * Fetches latest releases across all repos you own (viewer.repositories),
 * filters to last N days, then posts a digest to Telegram.
 */

const DAYS_DEFAULT = "7";
const RELEASES_PAGE_SIZE = 100;

const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID;
const GH_TOKEN = process.env.GH_TOKEN;
const days = parsePositiveInteger(
  process.env.INPUT_DAYS || process.env.DAYS_DEFAULT || DAYS_DEFAULT,
  "days",
);
const includePrereleases = String(process.env.INPUT_INCLUDE_PRERELEASES || "false").toLowerCase() === "true";

if (!TELEGRAM_BOT_TOKEN) throw new Error("Missing TELEGRAM_BOT_TOKEN");
if (!TELEGRAM_CHAT_ID) throw new Error("Missing TELEGRAM_CHAT_ID");
if (!GH_TOKEN) throw new Error("Missing GH_TOKEN");

const since = new Date(Date.now() - days * 24 * 60 * 60 * 1000);

async function ghGraphQL(query, variables) {
  const res = await fetch("https://api.github.com/graphql", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${GH_TOKEN}`,
      "Content-Type": "application/json",
      "User-Agent": "weekly-releases-to-telegram",
    },
    body: JSON.stringify({ query, variables }),
  });

  const json = await res.json();
  if (!res.ok) {
    throw new Error(`GitHub GraphQL HTTP ${res.status}: ${JSON.stringify(json)}`);
  }
  if (json.errors?.length) {
    throw new Error(`GitHub GraphQL errors: ${JSON.stringify(json.errors)}`);
  }
  return json.data;
}

async function telegramSend(text) {
  // Telegram limit is ~4096 chars; keep margin.
  const safe = text.length > 3800 ? text.slice(0, 3800) + "\n\n…(truncated)" : text;

  const url = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: TELEGRAM_CHAT_ID,
      text: safe,
      parse_mode: "HTML",
      disable_web_page_preview: true,
    }),
  });

  const json = await res.json();
  if (!res.ok || json.ok !== true) {
    throw new Error(`Telegram send failed: ${JSON.stringify(json)}`);
  }
}

const OWNED_REPOSITORIES_QUERY = `
query($cursor: String) {
  viewer {
    repositories(
      first: 100,
      after: $cursor,
      affiliations: [OWNER],
      isFork: false,
      orderBy: { field: UPDATED_AT, direction: DESC }
    ) {
      nodes {
        nameWithOwner
      }
      pageInfo { hasNextPage endCursor }
    }
  }
}
`;

const REPOSITORY_RELEASES_QUERY = `
query($owner: String!, $name: String!, $cursor: String, $pageSize: Int!) {
  repository(owner: $owner, name: $name) {
    releases(first: $pageSize, after: $cursor, orderBy: { field: CREATED_AT, direction: DESC }) {
      nodes {
        name
        tagName
        url
        publishedAt
        isDraft
        isPrerelease
      }
      pageInfo { hasNextPage endCursor }
    }
  }
}
`;

function parsePositiveInteger(rawValue, fieldName) {
  const value = Number.parseInt(rawValue, 10);
  if (!Number.isInteger(value) || value <= 0) {
    throw new Error(`Invalid ${fieldName}: "${rawValue}". Expected a positive integer.`);
  }

  return value;
}

function fmtDate(d) {
  return d.toISOString().slice(0, 10);
}

function pad2(value) {
  return String(value).padStart(2, "0");
}

function fmtDateShort(d) {
  return `${pad2(d.getUTCDate())}.${pad2(d.getUTCMonth() + 1)}.${d.getUTCFullYear()}`;
}

function formatPeriod(startDate, endDate) {
  const startDay = pad2(startDate.getUTCDate());
  const startMonth = pad2(startDate.getUTCMonth() + 1);
  const startYear = startDate.getUTCFullYear();
  const endDay = pad2(endDate.getUTCDate());
  const endMonth = pad2(endDate.getUTCMonth() + 1);
  const endYear = endDate.getUTCFullYear();

  if (startYear === endYear && startMonth === endMonth) {
    return `${startDay}-${endDay}.${endMonth}.${endYear}`;
  }

  if (startYear === endYear) {
    return `${startDay}.${startMonth}-${endDay}.${endMonth}.${endYear}`;
  }

  return `${fmtDateShort(startDate)}-${fmtDateShort(endDate)}`;
}

function daysBetweenUtc(startDate, endDate) {
  const startUtc = Date.UTC(startDate.getUTCFullYear(), startDate.getUTCMonth(), startDate.getUTCDate());
  const endUtc = Date.UTC(endDate.getUTCFullYear(), endDate.getUTCMonth(), endDate.getUTCDate());

  return Math.round((endUtc - startUtc) / (24 * 60 * 60 * 1000));
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function releaseTitle(r) {
  return (r.name && r.name.trim()) ? r.name.trim() : r.tagName;
}

function splitRepositoryName(repositoryNameWithOwner) {
  const [owner, name] = repositoryNameWithOwner.split("/");
  if (!owner || !name) {
    throw new Error(`Invalid repository name: "${repositoryNameWithOwner}"`);
  }

  return { owner, name };
}

async function fetchOwnedRepositories() {
  const repositories = [];
  let cursor = null;
  for (;;) {
    const data = await ghGraphQL(OWNED_REPOSITORIES_QUERY, { cursor });
    const repoNodes = data.viewer.repositories.nodes || [];
    repositories.push(...repoNodes.map(repo => repo.nameWithOwner));

    const pageInfo = data.viewer.repositories.pageInfo;
    if (!pageInfo.hasNextPage) break;
    cursor = pageInfo.endCursor;
  }

  return repositories;
}

async function fetchRecentReleases(repositoryNameWithOwner, sinceDate) {
  const all = [];
  const { owner, name } = splitRepositoryName(repositoryNameWithOwner);

  let cursor = null;
  for (;;) {
    const data = await ghGraphQL(REPOSITORY_RELEASES_QUERY, {
      owner,
      name,
      cursor,
      pageSize: RELEASES_PAGE_SIZE,
    });
    const releaseConnection = data.repository?.releases;
    if (!releaseConnection) break;

    const releases = releaseConnection.nodes || [];
    let hasPublishedAtOrAfterSince = false;
    let hasUnpublishedRelease = false;

    for (const release of releases) {
      if (!release.publishedAt) {
        hasUnpublishedRelease = true;
        continue;
      }

      const publishedAt = new Date(release.publishedAt);
      if (publishedAt >= sinceDate) {
        hasPublishedAtOrAfterSince = true;
      }

      if (release.isDraft) continue;
      if (!includePrereleases && release.isPrerelease) continue;
      if (publishedAt < sinceDate) continue;

      all.push({
        repo: repositoryNameWithOwner,
        title: releaseTitle(release),
        url: release.url,
        publishedAt,
      });
    }

    if (!releaseConnection.pageInfo.hasNextPage) break;
    if (!hasPublishedAtOrAfterSince && !hasUnpublishedRelease) break;

    cursor = releaseConnection.pageInfo.endCursor;
  }

  return all;
}

async function main() {
  const all = [];
  const repositories = await fetchOwnedRepositories();

  for (const repositoryNameWithOwner of repositories) {
    const releases = await fetchRecentReleases(repositoryNameWithOwner, since);
    all.push(...releases);
  }

  all.sort((a, b) => b.publishedAt - a.publishedAt);

  const now = new Date();
  const isWeeklyPeriod = daysBetweenUtc(since, now) === 7;
  const period = formatPeriod(since, now);
  const header = isWeeklyPeriod ? `Releases this week (${period})` : `Releases in ${period}`;

  let body;
  if (all.length === 0) {
    body = escapeHtml("No releases found in this period.");
  } else {
    body = all
      .map(r => `- ${escapeHtml(r.repo)}: ${escapeHtml(r.title)} (${fmtDate(r.publishedAt)})\n  ${escapeHtml(r.url)}`)
      .join("\n");
  }

  await telegramSend(`<b>${escapeHtml(header)}</b>\n\n${body}`);
  console.log(`Sent ${all.length} release(s) to Telegram.`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
