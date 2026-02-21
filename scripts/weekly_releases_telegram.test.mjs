import assert from "node:assert/strict";
import test from "node:test";

import { buildTelegramMessage } from "./weekly_releases_telegram.mjs";

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
