import { describe, expect, it } from 'vitest'
import { parseNotificationStreamMessage } from '@/lib/notificationStream'
import type { InAppNotification } from '@/types/alerts/notifications'

const valid: InAppNotification = {
  id: 'n1',
  user_id: 'user',
  alert_id: null,
  title: 'BTC broke $70,000',
  message: 'Fired',
  notification_type: 'price_alert',
  data: null,
  action_url: '/',
  read: false,
  is_archived: false,
  created_at: '2026-08-30T00:00:00.000Z',
  read_at: null,
}

describe('parseNotificationStreamMessage', () => {
  it('parses a well-formed notification frame', () => {
    expect(parseNotificationStreamMessage(JSON.stringify(valid))).toEqual(valid)
  })

  it('returns null for malformed JSON', () => {
    expect(parseNotificationStreamMessage('{ not json')).toBeNull()
  })

  it('returns null when required fields are missing', () => {
    expect(parseNotificationStreamMessage(JSON.stringify({ id: 'n1' }))).toBeNull()
  })
})
