import { getAlertStatusBadgeConfig } from '@/components/alerts/shared/alertStatusBadgeConfig'
import type { PriceAlert } from '@/types/alerts/priceAlert'
import { formatPriceAlertHeadline } from './priceAlertRule'

export type PriceAlertDeleteDetail = {
  label: string
  value: string
}

function formatNotifyChannels(alert: PriceAlert): string {
  const channels = [
    alert.notify_in_app ? 'In the app' : null,
    alert.notify_email ? 'Email' : null,
  ].filter((channel): channel is string => channel !== null)

  return channels.length > 0 ? channels.join(', ') : 'None'
}

/** Rows shown in the delete confirmation so the user can tell which rule they are removing. */
export function priceAlertDeleteDetails(alert: PriceAlert): PriceAlertDeleteDetail[] {
  const name = alert.name?.trim()
  const note = alert.description?.trim()
  const details: PriceAlertDeleteDetail[] = []

  if (name) {
    details.push({ label: 'Name', value: name })
  }

  details.push(
    {
      label: 'Rule',
      value: formatPriceAlertHeadline(alert.asset, alert.alert_type, alert.threshold_price),
    },
    {
      label: 'Status',
      value: getAlertStatusBadgeConfig(alert.status).label,
    },
    {
      label: 'Repeat',
      value: alert.one_time ? 'One-time' : 'Repeats',
    },
    {
      label: 'Notify',
      value: formatNotifyChannels(alert),
    },
  )

  if (note) {
    details.push({ label: 'Note', value: note })
  }

  return details
}
