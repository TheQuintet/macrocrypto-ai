import { describe, expect, it } from 'vitest'
import {
  toApiEventType,
  toUiEventType,
  toUiImpact,
  toUiSubscription,
} from '@/lib/alerts/macroEventMapping'

describe('macroEventMapping', () => {
  it('maps UI event types onto the alert-service lowercase values', () => {
    expect(toApiEventType('FED')).toBe('fed')
    expect(toUiEventType('cpi')).toBe('CPI')
    expect(toUiEventType('other')).toBeNull()
  })

  it('normalizes impact strings from the API', () => {
    expect(toUiImpact('medium')).toBe('MEDIUM')
    expect(toUiImpact(null)).toBeNull()
  })

  it('leaves fields the alert service omits as null', () => {
    expect(
      toUiSubscription(
        {
          id: 'live-fed',
          user_id: 'user-1',
          event_type: 'fed',
          subscribed: true,
          impact_filter: 'high',
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
        'user-1',
      ),
    ).toEqual({
      id: 'live-fed',
      user_id: 'user-1',
      event_type: 'FED',
      subscribed: true,
      impact_filter: 'HIGH',
      timing: null,
      one_time: null,
      notify_in_app: null,
      notify_email: null,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    })
  })

  it('drops unusable subscription payloads', () => {
    expect(toUiSubscription({ event_type: 'other' }, 'user-1')).toBeNull()
  })
})
