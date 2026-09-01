import { describe, expect, it } from 'vitest'
import {
  listContainsNotification,
  mergeIncomingNotification,
  unreadCountAfterIncoming,
} from '@/lib/alerts/mergeIncomingNotification'
import type { InAppNotification } from '@/types/alerts/notifications'

function notification(
  overrides: Partial<InAppNotification> = {},
): InAppNotification {
  return {
    id: 'n-new',
    user_id: 'user',
    alert_id: null,
    title: 'New',
    message: 'Fired',
    notification_type: 'price_alert',
    data: null,
    action_url: '/',
    read: false,
    is_archived: false,
    created_at: '2026-08-31T00:00:00.000Z',
    read_at: null,
    ...overrides,
  }
}

describe('mergeIncomingNotification', () => {
  it('prepends a new alert and keeps newest first', () => {
    const older = notification({
      id: 'n-old',
      created_at: '2026-08-01T00:00:00.000Z',
    })
    const incoming = notification()
    const merged = mergeIncomingNotification(
      {
        total: 1,
        limit: 50,
        offset: 0,
        notifications: [older],
      },
      incoming,
    )

    expect(merged.notifications.map((item) => item.id)).toEqual([
      'n-new',
      'n-old',
    ])
    expect(merged.total).toBe(2)
  })

  it('does not duplicate an alert that is already in the list', () => {
    const incoming = notification({ title: 'Updated' })
    const merged = mergeIncomingNotification(
      {
        total: 1,
        limit: 50,
        offset: 0,
        notifications: [notification({ title: 'Original' })],
      },
      incoming,
    )

    expect(merged.total).toBe(1)
    expect(merged.notifications[0]?.title).toBe('Updated')
  })
})

describe('unreadCountAfterIncoming', () => {
  it('increments only for a new unread alert', () => {
    expect(unreadCountAfterIncoming(2, notification(), false)).toBe(3)
    expect(unreadCountAfterIncoming(2, notification(), true)).toBe(2)
    expect(
      unreadCountAfterIncoming(2, notification({ read: true }), false),
    ).toBe(2)
  })
})

describe('listContainsNotification', () => {
  it('reports whether the id is already cached', () => {
    const current = {
      total: 1,
      limit: 50,
      offset: 0,
      notifications: [notification()],
    }

    expect(listContainsNotification(current, 'n-new')).toBe(true)
    expect(listContainsNotification(current, 'missing')).toBe(false)
    expect(listContainsNotification(undefined, 'n-new')).toBe(false)
  })
})
