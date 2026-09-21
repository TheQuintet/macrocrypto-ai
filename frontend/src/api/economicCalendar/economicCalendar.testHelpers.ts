import type { EconomicEvent } from '@/types/economicCalendar'

let nextId = 1

/** A high-impact CPI print at 13:30 UTC unless the test says otherwise. */
export function makeEconomicEvent(
  overrides: Partial<EconomicEvent> = {},
): EconomicEvent {
  return {
    id: nextId++,
    event_name: 'CPI release',
    event_type: 'cpi',
    event_date: '2026-03-12T13:30:00.000Z',
    impact_level: 'high',
    description: 'Monthly consumer price index.',
    dataSource: 'live',
    ...overrides,
  }
}
