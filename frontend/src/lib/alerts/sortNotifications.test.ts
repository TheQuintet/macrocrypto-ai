import { describe, expect, it } from 'vitest'
import { sortNotificationsByDateNewestFirst } from '@/lib/alerts/sortNotifications'
import type { InAppNotification } from '@/types/alerts/notifications'

function item(
  id: string,
  created_at: string,
): InAppNotification {
  return {
    id,
    user_id: 'user',
    alert_id: null,
    title: id,
    message: id,
    notification_type: 'price_alert',
    data: null,
    action_url: '/',
    read: false,
    is_archived: false,
    created_at,
    read_at: null,
  }
}

describe('sortNotificationsByDateNewestFirst', () => {
  it('orders by created_at descending', () => {
    const sorted = sortNotificationsByDateNewestFirst([
      item('old', '2026-01-01T00:00:00.000Z'),
      item('new', '2026-08-30T00:00:00.000Z'),
      item('mid', '2026-04-01T00:00:00.000Z'),
    ])

    expect(sorted.map((entry) => entry.id)).toEqual(['new', 'mid', 'old'])
  })
})
