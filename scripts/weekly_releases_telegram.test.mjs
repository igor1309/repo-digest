import assert from "node:assert/strict";
import test from "node:test";

import { buildReleaseLines, buildTelegramMessage } from "./weekly_releases_telegram.mjs";

function countOccurrences(text, token) {
  return text.split(token).length - 1;
}

test("buildTelegramMessage shouldRenderHeaderAndEmptyBody_onNoReleases", () => {
  const message = buildTelegramMessage("Releases this week (14-21.02.2026)", []);

  assert.equal(message, "<b>Releases this week (14-21.02.2026)</b>\n\nNo releases found in this period.");
});

test("buildTelegramMessage shouldKeepBalancedTags_onTruncation", () => {
  const releaseLines = [
    "- <a href=\"https://example.com/1\">repo/one: First release</a> (2026-02-21)",
    "- <a href=\"https://example.com/2\">repo/two: Second release</a> (2026-02-20)",
    "- <a href=\"https://example.com/3\">repo/three: Third release</a> (2026-02-19)",
  ];
  const message = buildTelegramMessage("Releases this week (14-21.02.2026)", releaseLines, { maxLength: 180 });

  assert.ok(message.endsWith("\n\n…(truncated)"));
  assert.ok(message.length <= 180);
  assert.equal(countOccurrences(message, "<a "), countOccurrences(message, "</a>"));
  assert.equal(countOccurrences(message, "<b>"), countOccurrences(message, "</b>"));
});

test("buildTelegramMessage shouldIncludeAllLines_onShortBody", () => {
  const releaseLines = [
    "- <a href=\"https://example.com/1\">repo/one: First release</a> (2026-02-21)",
    "- <a href=\"https://example.com/2\">repo/two: Second release</a> (2026-02-20)",
  ];
  const message = buildTelegramMessage("Releases this week (14-21.02.2026)", releaseLines, { maxLength: 1000 });

  assert.ok(!message.includes("…(truncated)"));
  assert.equal(countOccurrences(message, "\n"), 3);
  assert.equal(countOccurrences(message, "<a "), 2);
});

test("buildReleaseLines shouldGroupByRepositoryAndLinkVersionDate_onReleasesFromMultipleRepositories", () => {
  const releases = [
    { repo: "igor1309/trend-scout-agent", title: "v0.9.3", url: "https://example.com/r1", publishedAt: new Date("2026-02-21T10:00:00Z") },
    { repo: "igor1309/trend-scout-agent", title: "v0.9.2", url: "https://example.com/r2", publishedAt: new Date("2026-02-21T09:00:00Z") },
    { repo: "igor1309/repo-digest", title: "v1.0.0", url: "https://example.com/r3", publishedAt: new Date("2026-02-20T10:00:00Z") },
  ];

  assert.deepEqual(buildReleaseLines(releases), [
    "<i>igor1309/trend-scout-agent</i>",
    "- <a href=\"https://example.com/r1\">v0.9.3 (2026-02-21)</a>",
    "- <a href=\"https://example.com/r2\">v0.9.2 (2026-02-21)</a>",
    "",
    "<i>igor1309/repo-digest</i>",
    "- <a href=\"https://example.com/r3\">v1.0.0 (2026-02-20)</a>",
  ]);
});

test("buildReleaseLines shouldSortSemanticVersionsDescending_onUnsortedRepositoryReleases", () => {
  const releases = [
    { repo: "igor1309/trend-scout-agent", title: "v0.2.2", url: "https://example.com/r1", publishedAt: new Date("2026-02-21T10:00:00Z") },
    { repo: "igor1309/trend-scout-agent", title: "v0.15.10", url: "https://example.com/r2", publishedAt: new Date("2026-02-21T09:00:00Z") },
    { repo: "igor1309/trend-scout-agent", title: "v0.15.2", url: "https://example.com/r3", publishedAt: new Date("2026-02-21T08:00:00Z") },
    { repo: "igor1309/trend-scout-agent", title: "v0.9.3", url: "https://example.com/r4", publishedAt: new Date("2026-02-21T07:00:00Z") },
  ];

  assert.deepEqual(buildReleaseLines(releases), [
    "<i>igor1309/trend-scout-agent</i>",
    "- <a href=\"https://example.com/r2\">v0.15.10 (2026-02-21)</a>",
    "- <a href=\"https://example.com/r3\">v0.15.2 (2026-02-21)</a>",
    "- <a href=\"https://example.com/r4\">v0.9.3 (2026-02-21)</a>",
    "- <a href=\"https://example.com/r1\">v0.2.2 (2026-02-21)</a>",
  ]);
});
