import { afterEach, describe, expect, it } from 'vitest'
import {
  buildSimulatedNotifications,
  resetSimulatedNotifications,
  simulatedNotificationIds,
  simulateGetNotifications,
  simulateGetUnreadCount,
  simulateIncomingNotification,
  simulateMarkAllAsRead,
  simulateMarkAsRead,
} from '@/api/alerts/simulatedNotifications'
import { ALERTS_USER_ID } from '@/constants/alerts'

afterEach(() => {
  resetSimulatedNotifications()
})

describe('buildSimulatedNotifications', () => {
  it('seeds unread price, macro, and prediction examples', () => {
    const notifications = buildSimulatedNotifications()

    expect(notifications.length).toBeGreaterThan(0)
    expect(notifications.some((item) => !item.read)).toBe(true)
    expect(notifications.some((item) => item.read)).toBe(true)
    expect(
      notifications.some((item) => item.notification_type === 'price_alert'),
    ).toBe(true)
    expect(
      notifications.some((item) => item.notification_type === 'prediction_alert'),
    ).toBe(true)
    expect(
      notifications.some((item) => item.notification_type === 'macro_alert'),
    ).toBe(true)
    expect(
      notifications.every(
        (item, index, list) =>
          index === 0 ||
          Date.parse(list[index - 1]!.created_at) >= Date.parse(item.created_at),
      ),
    ).toBe(true)
  })
})

describe('simulateGetNotifications', () => {
  it('returns unread items when asked', async () => {
    const response = await simulateGetNotifications(ALERTS_USER_ID, {
      unread_only: true,
    })

    expect(response.notifications.every((item) => !item.read)).toBe(true)
    expect(response.total).toBeGreaterThan(0)
  })
})

describe('simulate notification reads', () => {
  it('marks one notification read and updates the unread count', async () => {
    const before = await simulateGetUnreadCount(ALERTS_USER_ID)
    await simulateMarkAsRead(simulatedNotificationIds.breakout)
    const after = await simulateGetUnreadCount(ALERTS_USER_ID)

    expect(after.count).toBe(before.count - 1)
  })

  it('marks every notification for the user as read', async () => {
    await simulateMarkAllAsRead(ALERTS_USER_ID)
    const unread = await simulateGetUnreadCount(ALERTS_USER_ID)

    expect(unread.count).toBe(0)
  })
})

describe('simulateIncomingNotification', () => {
  it('prepends a new unread alert for the user', async () => {
    const incoming = simulateIncomingNotification(ALERTS_USER_ID)
    const response = await simulateGetNotifications(ALERTS_USER_ID)

    expect(incoming.read).toBe(false)
    expect(response.notifications[0]?.id).toBe(incoming.id)
  })

  it('includes alert type, threshold, and trigger price on the first push', () => {
    const incoming = simulateIncomingNotification(ALERTS_USER_ID)

    expect(incoming.notification_type).toBe('price_alert')
    expect(incoming.data).toMatchObject({
      asset: 'BTC/USD',
      alert_type: 'crosses_above',
      threshold_price: expect.any(Number),
      triggered_price: expect.any(Number),
    })
    expect(incoming.title).toMatch(/BTC broke \$/)
  })

  it('rotates through macro and forecast alerts on later pushes', () => {
    simulateIncomingNotification(ALERTS_USER_ID)
    const macro = simulateIncomingNotification(ALERTS_USER_ID)
    const forecast = simulateIncomingNotification(ALERTS_USER_ID)

    expect(macro.notification_type).toBe('macro_alert')
    expect(macro.data).toMatchObject({
      event_name: 'Nonfarm Payrolls',
      impact: 'high',
    })
    expect(forecast.notification_type).toBe('prediction_alert')
    expect(forecast.data).toMatchObject({
      horizon: '24h',
      direction: 'bullish',
    })
  })
})
