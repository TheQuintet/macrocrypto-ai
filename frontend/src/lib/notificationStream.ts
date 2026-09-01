import type { InAppNotification } from '@/types/alerts/notifications'

/** First retry waits this long; each further attempt doubles it. */
export const NOTIFICATION_RECONNECT_BASE_DELAY_MS = 1_000

/** Ceiling so a long outage keeps retrying at a steady cadence. */
export const NOTIFICATION_RECONNECT_MAX_DELAY_MS = 16_000

export function notificationReconnectDelayMs(attempt: number) {
  const exponential =
    NOTIFICATION_RECONNECT_BASE_DELAY_MS * 2 ** Math.max(0, attempt - 1)

  return Math.min(exponential, NOTIFICATION_RECONNECT_MAX_DELAY_MS)
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

/**
 * Parse a notification frame off the wire.
 * Returns `null` for anything unreadable so a bad frame cannot take the
 * connection or the inbox down with it.
 */
export function parseNotificationStreamMessage(
  data: string,
): InAppNotification | null {
  let parsed: unknown

  try {
    parsed = JSON.parse(data)
  } catch {
    return null
  }

  if (!isRecord(parsed)) return null
  if (typeof parsed.id !== 'string') return null
  if (typeof parsed.user_id !== 'string') return null
  if (typeof parsed.title !== 'string') return null
  if (typeof parsed.message !== 'string') return null
  if (typeof parsed.created_at !== 'string') return null
  if (typeof parsed.read !== 'boolean') return null
  if (typeof parsed.notification_type !== 'string') return null

  return {
    id: parsed.id,
    user_id: parsed.user_id,
    alert_id: typeof parsed.alert_id === 'string' ? parsed.alert_id : null,
    title: parsed.title,
    message: parsed.message,
    notification_type: parsed.notification_type as InAppNotification['notification_type'],
    data: isRecord(parsed.data) ? parsed.data : null,
    action_url: typeof parsed.action_url === 'string' ? parsed.action_url : null,
    read: parsed.read,
    is_archived: parsed.is_archived === true,
    created_at: parsed.created_at,
    read_at: typeof parsed.read_at === 'string' ? parsed.read_at : null,
  }
}
