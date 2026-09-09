import { describe, expect, it } from 'vitest'
import { makeMacroSubscription } from '@/api/alerts/macroSubscriptions.testHelpers'
import { makeEconomicEvent } from '@/api/economicCalendar/economicCalendar.testHelpers'
import {
  activeSubscriptionsByType,
  filterEconomicEvents,
  isEventSubscribed,
} from '@/lib/economicEventFilters'

const fedHigh = makeEconomicEvent({
  event_name: 'FOMC rate decision',
  event_type: 'fed',
  impact_level: 'high',
})
const fedLow = makeEconomicEvent({
  event_name: 'Fed speech',
  event_type: 'fed',
  impact_level: 'low',
})
const cpiHigh = makeEconomicEvent({
  event_name: 'CPI release',
  event_type: 'cpi',
  impact_level: 'high',
})

describe('filterEconomicEvents', () => {
  const events = [fedHigh, fedLow, cpiHigh]

  it('keeps everything when both filters are all', () => {
    expect(
      filterEconomicEvents(events, { eventType: 'all', impactLevel: 'all' }),
    ).toHaveLength(3)
  })

  it('narrows to one event type', () => {
    const filtered = filterEconomicEvents(events, {
      eventType: 'fed',
      impactLevel: 'all',
    })

    expect(filtered.map((event) => event.event_name)).toEqual([
      'FOMC rate decision',
      'Fed speech',
    ])
  })

  it('narrows to one impact level', () => {
    const filtered = filterEconomicEvents(events, {
      eventType: 'all',
      impactLevel: 'low',
    })

    expect(filtered.map((event) => event.event_name)).toEqual(['Fed speech'])
  })

  it('applies both filters together', () => {
    const filtered = filterEconomicEvents(events, {
      eventType: 'fed',
      impactLevel: 'high',
    })

    expect(filtered.map((event) => event.event_name)).toEqual([
      'FOMC rate decision',
    ])
  })
})

describe('activeSubscriptionsByType', () => {
  it('ignores rows that record an unsubscribe', () => {
    const byType = activeSubscriptionsByType([
      makeMacroSubscription({ event_type: 'fed', subscribed: true }),
      makeMacroSubscription({
        id: 'subscription-2',
        event_type: 'cpi',
        subscribed: false,
      }),
    ])

    expect(byType.has('fed')).toBe(true)
    expect(byType.has('cpi')).toBe(false)
  })
})

describe('isEventSubscribed', () => {
  it('is false for a category with no subscription', () => {
    const byType = activeSubscriptionsByType([
      makeMacroSubscription({ event_type: 'fed' }),
    ])

    expect(isEventSubscribed(cpiHigh, byType)).toBe(false)
  })

  it('treats impact_filter as a floor, matching the alert engine', () => {
    // Subscribing at `high` alerts only on high-impact releases.
    const highOnly = activeSubscriptionsByType([
      makeMacroSubscription({ event_type: 'fed', impact_filter: 'high' }),
    ])

    expect(isEventSubscribed(fedHigh, highOnly)).toBe(true)
    expect(isEventSubscribed(fedLow, highOnly)).toBe(false)
  })

  it('alerts on everything in a category subscribed at the low floor', () => {
    const everything = activeSubscriptionsByType([
      makeMacroSubscription({ event_type: 'fed', impact_filter: 'low' }),
    ])

    expect(isEventSubscribed(fedHigh, everything)).toBe(true)
    expect(isEventSubscribed(fedLow, everything)).toBe(true)
  })

  it('is false when either level is outside the known scale', () => {
    const byType = activeSubscriptionsByType([
      makeMacroSubscription({
        event_type: 'fed',
        impact_filter: 'critical' as never,
      }),
    ])

    expect(isEventSubscribed(fedHigh, byType)).toBe(false)
    expect(
      isEventSubscribed(
        makeEconomicEvent({
          event_type: 'cpi',
          impact_level: 'critical' as never,
        }),
        activeSubscriptionsByType([
          makeMacroSubscription({ event_type: 'cpi', impact_filter: 'low' }),
        ]),
      ),
    ).toBe(false)
  })
})
