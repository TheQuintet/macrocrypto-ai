import { describe, expect, it } from 'vitest'
import { formatNotificationCopy, formatNotificationToast } from '@/lib/alerts/formatNotificationToast'
import type { InAppNotification } from '@/types/alerts/notifications'

const CREATED_AT = '2026-08-31T06:13:00.000Z'

function notification(
  overrides: Partial<InAppNotification> = {},
): InAppNotification {
  return {
    id: 'n-1',
    user_id: 'user-1',
    alert_id: null,
    title: 'BTC broke $72,000',
    message: 'BTC/USD went above $72,000.00',
    notification_type: 'price_alert',
    data: null,
    action_url: '/',
    read: false,
    is_archived: false,
    created_at: CREATED_AT,
    read_at: null,
    ...overrides,
  }
}

describe('formatNotificationToast', () => {
  it('exposes the same fields the inbox row uses', () => {
    const copy = formatNotificationCopy(
      notification({
        data: {
          name: 'BTC breakout',
          asset: 'BTC/USD',
          alert_type: 'crosses_above',
          threshold_price: 72_000,
          triggered_price: 72_140,
        },
      }),
    )

    expect(copy.typeLabel).toBe('Price alert')
    expect(copy.payload).toContain('BTC breakout')
    expect(copy.payload).toContain('BTC/USD went above $72,000.00 at $72,140.00')
    expect(copy.timestamp).toBeTruthy()
  })

  it('uses the notification title and names the alert type', () => {
    const toast = formatNotificationToast(notification())

    expect(toast.title).toBe('BTC broke $72,000')
    expect(toast.description).toContain('Price alert')
    expect(toast.description).toContain('BTC/USD went above $72,000.00')
  })

  it('adds asset, threshold, and trigger price for a price alert', () => {
    const toast = formatNotificationToast(
      notification({
        data: {
          name: 'BTC breakout',
          asset: 'BTC/USD',
          alert_type: 'crosses_above',
          threshold_price: 72_000,
          triggered_price: 72_140,
        },
      }),
    )

    expect(toast.description).toContain('BTC breakout')
    expect(toast.description).toContain(
      'BTC/USD went above $72,000.00 at $72,140.00',
    )
  })

  it('adds event and impact for a macro alert', () => {
    const toast = formatNotificationToast(
      notification({
        title: 'CPI print came in hot',
        message:
          'August CPI rose 0.3%. Higher inflation is typically negative for BTC.',
        notification_type: 'macro_alert',
        data: {
          event_name: 'CPI Release',
          impact: 'high',
          indicator: 'CPI',
        },
      }),
    )

    expect(toast.title).toBe('CPI print came in hot')
    expect(toast.description).toContain('Macro alert')
    expect(toast.description).toContain('CPI Release')
    expect(toast.description).toContain('high impact')
    expect(toast.description).toContain('August CPI rose 0.3%')
  })

  it('adds horizon and confidence for a forecast alert', () => {
    const toast = formatNotificationToast(
      notification({
        title: '24h outlook turned bullish',
        message: 'The model is leaning bullish for the next 24 hours.',
        notification_type: 'prediction_alert',
        data: { horizon: '24h', direction: 'bullish', confidence: 0.62 },
      }),
    )

    expect(toast.description).toContain('Forecast alert')
    expect(toast.description).toContain('24h')
    expect(toast.description).toContain('bullish')
    expect(toast.description).toContain('62% confidence')
  })

  it('appends leftover payload fields the typed formatter does not cover', () => {
    const toast = formatNotificationToast(
      notification({
        data: {
          name: 'BTC breakout',
          asset: 'BTC/USD',
          alert_type: 'crosses_above',
          threshold_price: 72_000,
          triggered_price: 72_140,
          exchange: 'Coinbase',
          source: 'alert_engine',
        },
      }),
    )

    expect(toast.description).toContain('exchange: Coinbase')
    expect(toast.description).toContain('source: alert_engine')
  })

  it('does not repeat the title as the body', () => {
    const toast = formatNotificationToast(
      notification({
        title: 'Same line',
        message: 'Same line',
        data: null,
      }),
    )

    expect(toast.description.split('\n').filter((line) => line === 'Same line')).toHaveLength(0)
  })
})
