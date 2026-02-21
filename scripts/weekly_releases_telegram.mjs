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

    for (const release of repositoryReleases) {
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
