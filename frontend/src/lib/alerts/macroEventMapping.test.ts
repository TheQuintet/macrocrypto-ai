import { describe, expect, it } from 'vitest'
import {
  toApiEventType,
  toUiEventType,
  toUiImpact,
  toUiMacroEvent,
  toUiSubscription,
  withDefaultSubscriptions,
} from '@/lib/alerts/macroEventMapping'
import type { EconomicEvent } from '@/types/economicCalendar'

describe('macroEventMapping', () => {
  it('maps UI event types onto the alert-service lowercase values', () => {
    expect(toApiEventType('FED')).toBe('fed')
    expect(toUiEventType('cpi')).toBe('CPI')
    expect(toUiEventType('other')).toBeNull()
  })

  it('normalizes impact strings from the API', () => {
    expect(toUiImpact('medium')).toBe('MEDIUM')
    expect(toUiImpact(null)).toBe('HIGH')
  })

  it('fills missing subscription rows so the toggle list stays complete', () => {
    const merged = withDefaultSubscriptions('user-1', [
      {
        id: 'live-fed',
        user_id: 'user-1',
        event_type: 'FED',
        subscribed: true,
        impact_filter: 'HIGH',
        timing: '1D',
        one_time: true,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      },
    ])

    expect(merged.map((row) => row.event_type)).toEqual([
      'FED',
      'CPI',
      'GDP',
      'EMPLOYMENT',
    ])
    expect(merged[0]?.subscribed).toBe(true)
    expect(merged[1]?.subscribed).toBe(false)
  })

  it('maps a calendar event into the alerts table shape', () => {
    const event: EconomicEvent = {
      id: 42,
      event_name: 'FOMC decision',
      event_type: 'fed',
      event_date: '2026-10-01T18:00:00Z',
      impact_level: 'high',
      description: 'Rate announcement',
      dataSource: 'live',
    }

    expect(toUiMacroEvent(event)).toMatchObject({
      id: '42',
      event_type: 'FED',
      impact: 'HIGH',
      scheduled_at: '2026-10-01T18:00:00Z',
      subscribed: false,
    })
  })

  it('drops unusable subscription payloads', () => {
    expect(toUiSubscription({ event_type: 'other' }, 'user-1')).toBeNull()
  })
})
