import { afterEach, describe, expect, it } from 'vitest'
import {
  buildSimulatedNotifications,
  resetSimulatedNotifications,
  simulatedNotificationIds,
  simulateGetNotifications,
  simulateGetUnreadCount,
  simulateMarkAllAsRead,
  simulateMarkAsRead,
} from '@/api/alerts/simulatedNotifications'
import { ALERTS_USER_ID } from '@/constants/alerts'

afterEach(() => {
  resetSimulatedNotifications()
})

describe('buildSimulatedNotifications', () => {
  it('seeds a mix of unread price alerts and an older read item', () => {
    const notifications = buildSimulatedNotifications()

    expect(notifications.length).toBeGreaterThan(0)
    expect(notifications.some((item) => !item.read)).toBe(true)
    expect(notifications.some((item) => item.read)).toBe(true)
    expect(
      notifications.some((item) => item.notification_type === 'price_alert'),
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
