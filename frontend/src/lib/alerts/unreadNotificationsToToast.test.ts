import { describe, expect, it } from 'vitest'
import { unreadNotificationsToToast } from './unreadNotificationsToToast'
import type { InAppNotification } from '@/types/alerts/notifications'

function notification(
  overrides: Partial<InAppNotification> = {},
): InAppNotification {
  return {
    id: 'n-1',
    user_id: 'user-1',
    alert_id: null,
    title: 'BTC broke $70,000',
    message: 'Price alert',
    notification_type: 'price_alert',
    data: null,
    action_url: '/',
    read: false,
    is_archived: false,
    created_at: '2026-08-31T12:00:00.000Z',
    read_at: null,
    ...overrides,
  }
}

describe('unreadNotificationsToToast', () => {
  it('returns only unread items so they can be stacked together', () => {
    const unread = notification({ id: 'unread' })
    const read = notification({ id: 'read', read: true, read_at: unread.created_at })

    expect(unreadNotificationsToToast([unread, read])).toEqual([unread])
  })

  it('returns oldest first so the newest toast sits on top of the pile', () => {
    const newer = notification({
      id: 'newer',
      created_at: '2026-08-31T13:00:00.000Z',
    })
    const older = notification({
      id: 'older',
      created_at: '2026-08-31T12:00:00.000Z',
    })

    expect(unreadNotificationsToToast([newer, older]).map((item) => item.id)).toEqual([
      'older',
      'newer',
    ])
  })

  it('returns an empty list when there is nothing to show', () => {
    expect(unreadNotificationsToToast(undefined)).toEqual([])
    expect(unreadNotificationsToToast([])).toEqual([])
  })
})
