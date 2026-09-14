import { describe, expect, it } from 'vitest'
import { makeEconomicEvent } from '@/api/economicCalendar/economicCalendar.testHelpers'
import { pastEvents, searchEventHistory } from '@/lib/economicEventHistory'
import { EMPTY_DATE_RANGE } from '@/lib/tableFilters'

const NOW = new Date('2026-03-15T12:00:00.000Z')

const cpi = makeEconomicEvent({
  event_name: 'CPI release',
  event_type: 'cpi',
  event_date: '2026-03-12T13:30:00.000Z',
})
const payrolls = makeEconomicEvent({
  event_name: 'Non-farm payrolls',
  event_type: 'employment',
  event_date: '2026-03-06T13:30:00.000Z',
  impact_level: 'medium',
})
const fomc = makeEconomicEvent({
  event_name: 'FOMC rate decision',
  event_type: 'fed',
  event_date: '2026-03-18T19:00:00.000Z',
})

describe('pastEvents', () => {
  it('keeps only events that have already happened', () => {
    expect(
      pastEvents([cpi, payrolls, fomc], NOW).map((event) => event.event_name),
    ).toEqual(['CPI release', 'Non-farm payrolls'])
  })

  it('orders them most recent first', () => {
    const ordered = pastEvents([payrolls, cpi], NOW)

    expect(ordered[0].event_name).toBe('CPI release')
  })

  it('leaves out an event whose date cannot be read', () => {
    expect(
      pastEvents([makeEconomicEvent({ event_date: 'not-a-date' })], NOW),
    ).toHaveLength(0)
  })

  it('treats an event happening right now as still upcoming', () => {
    const atNow = makeEconomicEvent({ event_date: NOW.toISOString() })

    expect(pastEvents([atNow], NOW)).toHaveLength(0)
  })
})

describe('searchEventHistory', () => {
  const history = pastEvents([cpi, payrolls], NOW)

  it('keeps everything when nothing is searched or ranged', () => {
    expect(
      searchEventHistory(
        history,
        { search: '', dateRange: EMPTY_DATE_RANGE },
        'UTC',
      ),
    ).toHaveLength(2)
  })

  it('searches the event name', () => {
    expect(
      searchEventHistory(
        history,
        { search: 'payrolls', dateRange: EMPTY_DATE_RANGE },
        'UTC',
      ).map((event) => event.event_name),
    ).toEqual(['Non-farm payrolls'])
  })

  it('ranges over the event date inclusively', () => {
    expect(
      searchEventHistory(
        history,
        { search: '', dateRange: { start: '2026-03-12', end: '2026-03-12' } },
        'UTC',
      ).map((event) => event.event_name),
    ).toEqual(['CPI release'])
  })

  it('applies search and range together', () => {
    expect(
      searchEventHistory(
        history,
        {
          search: 'cpi',
          dateRange: { start: '2026-03-01', end: '2026-03-07' },
        },
        'UTC',
      ),
    ).toHaveLength(0)
  })
})
