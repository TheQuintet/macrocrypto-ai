import { describe, expect, it } from 'vitest';
import {
  clampPage,
  isWithinDateRange,
  matchesSearch,
  pageCount,
  paginate,
  toCsv,
} from '@/lib/tableFilters';

const NEW_YORK = 'America/New_York';

describe('isWithinDateRange', () => {
  const instant = '2026-03-12T13:30:00.000Z';

  it('keeps everything when no bounds are set', () => {
    expect(
      isWithinDateRange(instant, { start: '', end: '' }, 'UTC'),
    ).toBe(true);
  });

  it('includes the boundary days', () => {
    expect(
      isWithinDateRange(instant, { start: '2026-03-12', end: '' }, 'UTC'),
    ).toBe(true);
    expect(
      isWithinDateRange(instant, { start: '', end: '2026-03-12' }, 'UTC'),
    ).toBe(true);
  });

  it('excludes instants outside the bounds', () => {
    expect(
      isWithinDateRange(instant, { start: '2026-03-13', end: '' }, 'UTC'),
    ).toBe(false);
    expect(
      isWithinDateRange(instant, { start: '', end: '2026-03-11' }, 'UTC'),
    ).toBe(false);
  });

  it('judges the day in the display timezone, not UTC', () => {
    // 00:30 UTC on the 2nd is still the evening of the 1st in New York, so a
    // range starting on the 2nd must not claim it.
    const overnight = '2026-03-02T00:30:00.000Z';
    const range = { start: '2026-03-02', end: '2026-03-02' };

    expect(isWithinDateRange(overnight, range, 'UTC')).toBe(true);
    expect(isWithinDateRange(overnight, range, NEW_YORK)).toBe(false);
  });

  it('keeps an unreadable date until a range is set, then drops it', () => {
    expect(
      isWithinDateRange(null, { start: '', end: '' }, 'UTC'),
    ).toBe(true);
    expect(
      isWithinDateRange('not-a-date', { start: '', end: '' }, 'UTC'),
    ).toBe(true);
    expect(
      isWithinDateRange(null, { start: '2026-03-01', end: '' }, 'UTC'),
    ).toBe(false);
  });
});

describe('matchesSearch', () => {
  it('matches any field, case-insensitively', () => {
    expect(matchesSearch('cpi', ['CPI release', 'Inflation'])).toBe(true);
    expect(matchesSearch('INFLA', ['CPI release', 'Inflation'])).toBe(true);
  });

  it('keeps every row for a blank or whitespace query', () => {
    expect(matchesSearch('', ['anything'])).toBe(true);
    expect(matchesSearch('   ', ['anything'])).toBe(true);
  });

  it('ignores missing fields rather than throwing', () => {
    expect(matchesSearch('cpi', [null, undefined, 'CPI'])).toBe(true);
    expect(matchesSearch('gdp', [null, undefined])).toBe(false);
  });
});

describe('pagination', () => {
  const rows = Array.from({ length: 23 }, (_, index) => index + 1);

  it('always reports at least one page', () => {
    expect(pageCount(0, 10)).toBe(1);
    expect(pageCount(23, 10)).toBe(3);
  });

  it('clamps a page into range', () => {
    expect(clampPage(0, 3)).toBe(1);
    expect(clampPage(9, 3)).toBe(3);
    expect(clampPage(2, 3)).toBe(2);
  });

  it('slices the requested page', () => {
    expect(paginate(rows, 1, 10)).toHaveLength(10);
    expect(paginate(rows, 1, 10)[0]).toBe(1);
    expect(paginate(rows, 3, 10)).toEqual([21, 22, 23]);
  });

  it('falls back to the last page rather than showing nothing', () => {
    // Filtering down while on page 3 must not leave the reader staring at
    // an empty table.
    expect(paginate(rows.slice(0, 5), 3, 10)).toEqual([1, 2, 3, 4, 5]);
  });
});

describe('toCsv', () => {
  it('quotes every field so separators inside a value cannot shift columns', () => {
    const csv = toCsv(
      ['Event', 'Note'],
      [['CPI release', 'Hot print, risk-off']],
    );

    expect(csv).toBe('"Event","Note"\r\n"CPI release","Hot print, risk-off"');
  });

  it('doubles embedded quotes', () => {
    expect(toCsv(['Note'], [['He said "buy"']])).toContain(
      '"He said ""buy"""',
    );
  });
});
