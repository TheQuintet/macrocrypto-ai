import { afterEach, describe, expect, it } from 'vitest'
import { notificationApi } from '@/api/alerts/notifications'
import { priceAlertApi } from '@/api/alerts/priceAlerts'
import { resetSimulatedNotifications } from '@/api/alerts/simulatedNotifications'
import { resetSimulatedPriceAlerts } from '@/api/alerts/simulatedPriceAlerts'
import { ALERTS_USER_ID } from '@/constants/alerts'

afterEach(() => {
  resetSimulatedPriceAlerts()
  resetSimulatedNotifications()
})

describe('alert APIs without a backend', () => {
  it('lists simulated price alerts', async () => {
    const response = await priceAlertApi.getAlerts(ALERTS_USER_ID)

    expect(response.alerts.length).toBeGreaterThan(0)
    expect(response.alerts[0]?.asset).toBe('BTC/USD')
  })

  it('lists simulated notifications and an unread count', async () => {
    const [list, unread] = await Promise.all([
      notificationApi.getNotifications(ALERTS_USER_ID),
      notificationApi.getUnreadCount(ALERTS_USER_ID),
    ])

    expect(list.notifications.length).toBeGreaterThan(0)
    expect(unread.count).toBeGreaterThan(0)
  })
})
