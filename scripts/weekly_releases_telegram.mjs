const TELEGRAM_SOFT_LIMIT = 3800;
const TRUNCATION_SUFFIX = "\n\n…(truncated)";

export function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function fmtDate(date) {
  return date.toISOString().slice(0, 10);
}

function parseSemanticVersion(title) {
  const match = String(title).trim().match(/^v?(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$/);
  if (!match) {
    return null;
  }

  return {
    major: Number.parseInt(match[1], 10),
    minor: Number.parseInt(match[2], 10),
    patch: Number.parseInt(match[3], 10),
  };
}

function compareSemanticVersionDesc(leftTitle, rightTitle) {
  const leftVersion = parseSemanticVersion(leftTitle);
  const rightVersion = parseSemanticVersion(rightTitle);

  if (leftVersion && rightVersion) {
    if (leftVersion.major !== rightVersion.major) return rightVersion.major - leftVersion.major;
    if (leftVersion.minor !== rightVersion.minor) return rightVersion.minor - leftVersion.minor;
    if (leftVersion.patch !== rightVersion.patch) return rightVersion.patch - leftVersion.patch;
    return 0;
  }

  if (leftVersion) return -1;
  if (rightVersion) return 1;
  return 0;
}

function compareReleaseOrder(left, right) {
  const semanticVersionOrder = compareSemanticVersionDesc(left.title, right.title);
  if (semanticVersionOrder !== 0) {
    return semanticVersionOrder;
  }

  const publishedAtOrder = right.publishedAt.getTime() - left.publishedAt.getTime();
  if (publishedAtOrder !== 0) {
    return publishedAtOrder;
  }

  return left.title.localeCompare(right.title);
}

export function buildReleaseLines(releases) {
  const releasesByRepository = new Map();

  for (const release of releases) {
    const repositoryReleases = releasesByRepository.get(release.repo) || [];
    repositoryReleases.push(release);
    releasesByRepository.set(release.repo, repositoryReleases);
  }

  const lines = [];
  let isFirstRepository = true;

  for (const [repositoryName, repositoryReleases] of releasesByRepository.entries()) {
    if (!isFirstRepository) {
      lines.push("");
    }

    lines.push(`<i>${escapeHtml(repositoryName)}</i>`);

    const sortedReleases = [...repositoryReleases].sort(compareReleaseOrder);

    for (const release of sortedReleases) {
      const releaseLabel = `${release.title} (${fmtDate(release.publishedAt)})`;
      lines.push(`- <a href="${escapeHtml(release.url)}">${escapeHtml(releaseLabel)}</a>`);
    }

    isFirstRepository = false;
  }

  return lines;
}

function appendLinesWithinLimit(prefix, lines, maxLength) {
  let message = prefix;

  for (let index = 0; index < lines.length; index += 1) {
    const separator = index === 0 ? "" : "\n";
    const next = `${message}${separator}${lines[index]}`;
    const hasMoreLines = index < lines.length - 1;
    const projectedLength = next.length + (hasMoreLines ? TRUNCATION_SUFFIX.length : 0);

    if (projectedLength > maxLength) {
      if (message.length + TRUNCATION_SUFFIX.length <= maxLength) {
        return `${message}${TRUNCATION_SUFFIX}`;
      }

      return message;
    }

    message = next;
  }

  return message;
}

export function buildTelegramMessage(header, releaseLines, options = {}) {
  const maxLength = options.maxLength || TELEGRAM_SOFT_LIMIT;
  const noReleasesText = options.noReleasesText || "No releases found in this period.";
  const prefix = `<b>${escapeHtml(header)}</b>\n\n`;

  if (releaseLines.length === 0) {
    return `${prefix}${escapeHtml(noReleasesText)}`;
  }

  return appendLinesWithinLimit(prefix, releaseLines, maxLength);
}
