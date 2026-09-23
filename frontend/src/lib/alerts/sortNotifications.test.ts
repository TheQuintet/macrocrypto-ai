import { describe, expect, it } from 'vitest'
import {
  sortNotificationsByDateNewestFirst,
  splitNotificationsByRead,
} from '@/lib/alerts/sortNotifications'
import type { InAppNotification } from '@/types/alerts/notifications'

function item(
  id: string,
  created_at: string,
  read = false,
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
    read,
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

describe('splitNotificationsByRead', () => {
  it('keeps unread rows separate from read ones', () => {
    const { unread, read } = splitNotificationsByRead([
      item('open', '2026-08-30T00:00:00.000Z', false),
      item('done', '2026-08-29T00:00:00.000Z', true),
    ])

    expect(unread.map((entry) => entry.id)).toEqual(['open'])
    expect(read.map((entry) => entry.id)).toEqual(['done'])
  })
})
