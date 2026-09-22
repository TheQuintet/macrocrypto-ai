import { describe, expect, it } from 'vitest';
import { makeMacroAlertHistoryEntry } from '@/api/alerts/macroAlertHistory.testHelpers';
import {
  filterMacroAlertHistory,
  formatAlertTiming,
  macroAlertHistoryToCsv,
  sortMacroAlertHistory,
} from '@/lib/alerts/macroAlertHistoryFilters';
import { EMPTY_DATE_RANGE } from '@/lib/tableFilters';

const cpi = makeMacroAlertHistoryEntry({
  event_name: 'CPI release',
  event_type: 'cpi',
  sent_at: '2026-03-11T13:30:00.000Z',
});
const fomc = makeMacroAlertHistoryEntry({
  event_name: 'FOMC rate decision',
  event_type: 'fed',
  timing: '12h',
  sent_at: '2026-03-18T07:00:00.000Z',
});
const payrolls = makeMacroAlertHistoryEntry({
  event_name: 'Non-farm payrolls',
  event_type: 'employment',
  sent_at: '2026-03-05T13:30:00.000Z',
});

const allEntries = [cpi, fomc, payrolls];
const noFilters = {
  search: '',
  eventType: 'all' as const,
  dateRange: EMPTY_DATE_RANGE,
};

describe('formatAlertTiming', () => {
  it('spells out the lead time', () => {
    expect(formatAlertTiming('1d')).toBe('1 day before');
    expect(formatAlertTiming('12h')).toBe('12 hours before');
    expect(formatAlertTiming('1h')).toBe('1 hour before');
  });

  it('passes through a lead time it does not know', () => {
    expect(formatAlertTiming('30m')).toBe('30m');
  });
});

describe('sortMacroAlertHistory', () => {
  it('puts the most recently sent alert first', () => {
    expect(
      sortMacroAlertHistory(allEntries).map((entry) => entry.event_name),
    ).toEqual(['FOMC rate decision', 'CPI release', 'Non-farm payrolls']);
  });

  it('sinks entries with no sent date to the bottom', () => {
    const undated = makeMacroAlertHistoryEntry({
      event_name: 'Unknown',
      sent_at: null,
    });

    expect(
      sortMacroAlertHistory([undated, cpi]).map((entry) => entry.event_name),
    ).toEqual(['CPI release', 'Unknown']);
  });

  it('does not mutate the input', () => {
    const input = [cpi, fomc];
    sortMacroAlertHistory(input);

    expect(input[0].event_name).toBe('CPI release');
  });
});

describe('filterMacroAlertHistory', () => {
  it('keeps everything when nothing is filtered', () => {
    expect(
      filterMacroAlertHistory(allEntries, noFilters, 'UTC'),
    ).toHaveLength(3);
  });

  it('narrows to one event type', () => {
    expect(
      filterMacroAlertHistory(
        allEntries,
        { ...noFilters, eventType: 'fed' },
        'UTC',
      ).map((entry) => entry.event_name),
    ).toEqual(['FOMC rate decision']);
  });

  it('searches the event name', () => {
    expect(
      filterMacroAlertHistory(
        allEntries,
        { ...noFilters, search: 'payrolls' },
        'UTC',
      ).map((entry) => entry.event_name),
    ).toEqual(['Non-farm payrolls']);
  });

  it('searches the readable category label, not just the raw code', () => {
    expect(
      filterMacroAlertHistory(
        allEntries,
        { ...noFilters, search: 'employment' },
        'UTC',
      ),
    ).toHaveLength(1);
  });

  it('ranges over the sent date, not the event date', () => {
    const filtered = filterMacroAlertHistory(
      allEntries,
      {
        ...noFilters,
        dateRange: { start: '2026-03-10', end: '2026-03-20' },
      },
      'UTC',
    );

    expect(filtered.map((entry) => entry.event_name)).toEqual([
      'CPI release',
      'FOMC rate decision',
    ]);
  });

  it('applies search and category together', () => {
    expect(
      filterMacroAlertHistory(
        allEntries,
        { ...noFilters, search: 'release', eventType: 'fed' },
        'UTC',
      ),
    ).toHaveLength(0);
  });
});

describe('macroAlertHistoryToCsv', () => {
  it('exports a header row and one row per alert', () => {
    const csv = macroAlertHistoryToCsv([cpi], 'UTC');
    const [header, row] = csv.split('\r\n');

    expect(header).toBe(
      '"Event","Event type","Event date","Impact","Alert timing","Sent"',
    );
    expect(row).toContain('"CPI release"');
    expect(row).toContain('"1 day before"');
    expect(row).toContain('"CPI"');
  });

  it('says so rather than leaving a date blank', () => {
    const csv = macroAlertHistoryToCsv(
      [makeMacroAlertHistoryEntry({ sent_at: null, event_date: null })],
      'UTC',
    );

    expect(csv).toContain('"Date unavailable"');
  });
});
