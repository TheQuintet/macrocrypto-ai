import { getAlertStatusBadgeConfig } from '@/components/alerts/shared/alertStatusBadgeConfig'
import type { PredictionAlert } from '@/types/alerts/predictionAlert'
import {
  formatPredictionAlertHeadline,
} from './predictionAlertRule'

export type PredictionAlertDeleteDetail = {
  label: string
  value: string
}

function formatNotifyChannels(alert: PredictionAlert): string {
  const channels = [
    alert.notify_in_app ? 'In the app' : null,
    alert.notify_email ? 'Email' : null,
  ].filter((channel): channel is string => channel !== null)

  return channels.length > 0 ? channels.join(', ') : 'None'
}

/** Rows shown in the delete confirmation so the user can tell which rule they are removing. */
export function predictionAlertDeleteDetails(
  alert: PredictionAlert,
): PredictionAlertDeleteDetail[] {
  const name = alert.name?.trim()
  const note = alert.description?.trim()
  const details: PredictionAlertDeleteDetail[] = []

  if (name) {
    details.push({ label: 'Name', value: name })
  }

  details.push(
    {
      label: 'Rule',
      value: formatPredictionAlertHeadline(alert.threshold, alert.horizon),
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
