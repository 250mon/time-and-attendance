/** Calendar years available for leave balances (from hire year through `throughYear`). */
export function calendarYearsFromHire(
  hireDateIso: string | null | undefined,
  throughYear: number,
): number[] {
  const startYear = hireDateIso
    ? new Date(hireDateIso + "T00:00:00").getFullYear()
    : throughYear;
  const years: number[] = [];
  for (let y = startYear; y <= throughYear; y++) {
    years.push(y);
  }
  return years;
}

/** Inclusive calendar-year window [Jan 1, next Jan 1). */
export function calendarYearPeriod(year: number): { start: Date; end: Date } {
  return {
    start: new Date(year, 0, 1),
    end: new Date(year + 1, 0, 1),
  };
}

export function isDateInCalendarYear(dateIso: string, year: number): boolean {
  const d = new Date(dateIso + "T00:00:00");
  const { start, end } = calendarYearPeriod(year);
  return d >= start && d < end;
}
