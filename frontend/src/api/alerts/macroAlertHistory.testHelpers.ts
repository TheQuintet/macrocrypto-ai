import type { MacroAlertHistoryEntry } from '@/types/alerts/macroAlertHistory';

let nextId = 1;

/** A high-impact CPI alert sent a day before the release, unless overridden. */
export function makeMacroAlertHistoryEntry(
  overrides: Partial<MacroAlertHistoryEntry> = {},
): MacroAlertHistoryEntry {
  return {
    id: `macro-notification-${nextId++}`,
    user_id: 'user-1',
    alert_id: 'macro-alert-1',
    event_name: 'CPI release',
    event_type: 'cpi',
    event_date: '2026-03-12T13:30:00.000Z',
    timing: '1d',
    impact: 'high',
    description: 'Monthly consumer price index.',
    read: true,
    sent_at: '2026-03-11T13:30:00.000Z',
    ...overrides,
  };
}
