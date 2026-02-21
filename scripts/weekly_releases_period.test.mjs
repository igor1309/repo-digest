import assert from "node:assert/strict";
import test from "node:test";

import { buildHeader, daysBetweenUtc, formatPeriod } from "./weekly_releases_period.mjs";

function makeUtcDate(year, month, day) {
  return new Date(Date.UTC(year, month - 1, day));
}

test("formatPeriod shouldReturnDayDayMonthYear_onDatesWithinOneMonth", () => {
  const startDate = makeUtcDate(2026, 2, 14);
  const endDate = makeUtcDate(2026, 2, 21);

  assert.equal(formatPeriod(startDate, endDate), "14-21.02.2026");
});

test("formatPeriod shouldReturnDayMonthDayMonthYear_onDatesWithinOneYear", () => {
  const startDate = makeUtcDate(2026, 2, 28);
  const endDate = makeUtcDate(2026, 3, 2);

  assert.equal(formatPeriod(startDate, endDate), "28.02-02.03.2026");
});

test("formatPeriod shouldReturnFullDates_onDatesAcrossDifferentYears", () => {
  const startDate = makeUtcDate(2025, 12, 31);
  const endDate = makeUtcDate(2026, 1, 1);

  assert.equal(formatPeriod(startDate, endDate), "31.12.2025-01.01.2026");
});

test("buildHeader shouldReturnWeeklyTitle_onExactSevenDayPeriod", () => {
  const startDate = makeUtcDate(2026, 2, 14);
  const endDate = makeUtcDate(2026, 2, 21);

  assert.equal(daysBetweenUtc(startDate, endDate), 7);
  assert.equal(buildHeader(startDate, endDate), "Releases this week (14-21.02.2026)");
});

test("buildHeader shouldReturnGenericTitle_onNonSevenDayPeriod", () => {
  const startDate = makeUtcDate(2026, 2, 14);
  const endDate = makeUtcDate(2026, 2, 20);

  assert.equal(daysBetweenUtc(startDate, endDate), 6);
  assert.equal(buildHeader(startDate, endDate), "Releases in 14-20.02.2026");
});
