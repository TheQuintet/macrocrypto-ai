import { formatPrice } from '@/components/dashboard/lib/priceFormat'
import type {
  InAppNotification,
  NotificationType,
} from '@/types/alerts/notifications'

const TYPE_LABEL: Record<NotificationType, string> = {
  price_alert: 'Price alert',
  prediction_alert: 'Forecast alert',
  confidence_alert: 'Confidence alert',
  macro_alert: 'Macro alert',
}

const PRICE_ALERT_VERB: Record<string, string> = {
  reaches: 'hit',
  crosses_above: 'went above',
  crosses_below: 'went below',
}

export type NotificationCopy = {
  title: string
  typeLabel: string
  payload?: string
  message?: string
  timestamp?: string
}

/** Structured copy shared by the inbox row and the toast. */
export function formatNotificationCopy(
  notification: InAppNotification,
): NotificationCopy {
  const payload = formatPayloadDetails(notification)
  const shouldIncludeMessage =
    Boolean(notification.message) &&
    notification.message !== notification.title &&
    notification.message !== payload &&
    !(notification.notification_type === 'price_alert' && payload)

  return {
    title: notification.title,
    typeLabel: TYPE_LABEL[notification.notification_type],
    payload,
    message: shouldIncludeMessage ? notification.message : undefined,
    timestamp: formatNotificationTimestamp(notification.created_at),
  }
}

/** Title + multi-line body for the in-app toast of a newly arrived alert. */
export function formatNotificationToast(notification: InAppNotification): {
  title: string
  description: string
} {
  const copy = formatNotificationCopy(notification)
  return {
    title: copy.title,
    description: [
      copy.typeLabel,
      copy.payload,
      copy.message,
      copy.timestamp,
    ]
      .filter((line): line is string => Boolean(line))
      .join('\n'),
  }
}

const PAYLOAD_KEYS: Record<NotificationType, readonly string[]> = {
  price_alert: ['name', 'asset', 'alert_type', 'threshold_price', 'triggered_price'],
  prediction_alert: ['horizon', 'direction', 'confidence'],
  confidence_alert: ['horizon', 'direction', 'confidence'],
  macro_alert: ['event_name', 'indicator', 'impact'],
}

function formatPayloadDetails(notification: InAppNotification): string | undefined {
  const data = notification.data
  if (!data) return undefined

  const typed = (() => {
    switch (notification.notification_type) {
      case 'price_alert':
        return formatPriceAlertDetails(data)
      case 'macro_alert':
        return formatMacroAlertDetails(data)
      case 'prediction_alert':
      case 'confidence_alert':
        return formatForecastAlertDetails(data)
      default:
        return undefined
    }
  })()

  const leftover = formatLeftoverDetails(
    data,
    PAYLOAD_KEYS[notification.notification_type],
  )

  const parts = [typed, leftover].filter((line): line is string => Boolean(line))
  return parts.length > 0 ? parts.join('\n') : undefined
}

function formatLeftoverDetails(
  data: Record<string, unknown>,
  usedKeys: readonly string[],
): string | undefined {
  const used = new Set(usedKeys)
  const lines: string[] = []

  for (const [key, value] of Object.entries(data)) {
    if (used.has(key)) continue
    const formatted = formatDataValue(value)
    if (!formatted) continue
    lines.push(`${humanizeKey(key)}: ${formatted}`)
  }

  return lines.length > 0 ? lines.join('\n') : undefined
}

function humanizeKey(key: string): string {
  return key.replaceAll('_', ' ')
}

function formatDataValue(value: unknown): string | undefined {
  if (typeof value === 'string' && value.trim()) return value.trim()
  if (typeof value === 'number' && Number.isFinite(value)) return String(value)
  if (typeof value === 'boolean') return value ? 'yes' : 'no'
  return undefined
}

function formatPriceAlertDetails(
  data: Record<string, unknown>,
): string | undefined {
  const asset = asNonEmptyString(data.asset) ?? 'BTC/USD'
  const name = asNonEmptyString(data.name)
  const threshold = asFiniteNumber(data.threshold_price)
  const triggered = asFiniteNumber(data.triggered_price)
  const verb = PRICE_ALERT_VERB[asNonEmptyString(data.alert_type) ?? '']

  const parts: string[] = []
  if (name) parts.push(name)

  if (threshold != null && triggered != null && verb) {
    parts.push(
      `${asset} ${verb} ${formatPrice(threshold)} at ${formatPrice(triggered)}`,
    )
  } else if (threshold != null && triggered != null) {
    parts.push(
      `${asset} traded at ${formatPrice(triggered)} (threshold ${formatPrice(threshold)})`,
    )
  } else if (triggered != null) {
    parts.push(`${asset} traded at ${formatPrice(triggered)}`)
  } else if (threshold != null) {
    parts.push(`${asset} threshold ${formatPrice(threshold)}`)
  }

  return parts.length > 0 ? parts.join('\n') : undefined
}

function formatMacroAlertDetails(
  data: Record<string, unknown>,
): string | undefined {
  const eventName = asNonEmptyString(data.event_name)
  const indicator = asNonEmptyString(data.indicator)
  const impact = asNonEmptyString(data.impact)
  const headline = eventName ?? indicator
  if (!headline && !impact) return undefined

  const parts = [headline]
  if (impact) parts.push(`${impact} impact`)
  return parts.filter(Boolean).join(' · ')
}

function formatForecastAlertDetails(
  data: Record<string, unknown>,
): string | undefined {
  const horizon = asNonEmptyString(data.horizon)
  const direction = asNonEmptyString(data.direction)
  const confidence = asFiniteNumber(data.confidence)
  const parts: string[] = []
  if (horizon) parts.push(horizon)
  if (direction) parts.push(direction)
  if (confidence != null) {
    parts.push(`${Math.round(confidence * 100)}% confidence`)
  }
  return parts.length > 0 ? parts.join(' · ') : undefined
}

function formatNotificationTimestamp(iso: string): string | undefined {
  const parsed = new Date(iso)
  if (Number.isNaN(parsed.getTime())) return undefined

  return parsed.toLocaleString('en-GB', {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

function asFiniteNumber(value: unknown): number | undefined {
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value)
    if (Number.isFinite(parsed)) return parsed
  }
  return undefined
}

function asNonEmptyString(value: unknown): string | undefined {
  if (typeof value === 'string' && value.trim()) return value.trim()
  return undefined
}
