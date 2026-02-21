function pad2(value) {
  return String(value).padStart(2, "0");
}

function fmtDateShort(date) {
  return `${pad2(date.getUTCDate())}.${pad2(date.getUTCMonth() + 1)}.${date.getUTCFullYear()}`;
}

export function formatPeriod(startDate, endDate) {
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

export function daysBetweenUtc(startDate, endDate) {
  const startUtc = Date.UTC(startDate.getUTCFullYear(), startDate.getUTCMonth(), startDate.getUTCDate());
  const endUtc = Date.UTC(endDate.getUTCFullYear(), endDate.getUTCMonth(), endDate.getUTCDate());

  return Math.round((endUtc - startUtc) / (24 * 60 * 60 * 1000));
}

export function buildHeader(startDate, endDate) {
  const period = formatPeriod(startDate, endDate);
  const isWeeklyPeriod = daysBetweenUtc(startDate, endDate) === 7;

  return isWeeklyPeriod ? `Releases this week (${period})` : `Releases in ${period}`;
}
