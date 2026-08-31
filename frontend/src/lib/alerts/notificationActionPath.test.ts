import { describe, expect, it } from 'vitest'
import { routes } from '@/constants/navigation'
import { notificationActionPath } from '@/lib/alerts/notificationActionPath'
import type { InAppNotification } from '@/types/alerts/notifications'

function notification(
  notification_type: InAppNotification['notification_type'],
): InAppNotification {
  return {
    id: 'n1',
    user_id: 'user',
    alert_id: null,
    title: 'Alert',
    message: 'Fired',
    notification_type,
    data: null,
    action_url: '/alerts/ignored',
    read: false,
    is_archived: false,
    created_at: '2026-08-30T00:00:00.000Z',
    read_at: null,
  }
}

describe('notificationActionPath', () => {
  it('sends price alerts to the chart', () => {
    expect(notificationActionPath(notification('price_alert'))).toBe(
      routes.dashboard,
    )
  })

  it('sends prediction alerts to forecasts', () => {
    expect(notificationActionPath(notification('prediction_alert'))).toBe(
      routes.forecasts,
    )
  })

  it('sends macro alerts to the macro page', () => {
    expect(notificationActionPath(notification('macro_alert'))).toBe(
      routes.macro,
    )
  })
})
