import type { AlertStatus } from '@/types/alerts/priceAlert'

const ALERT_STATUSES: AlertStatus[] = ['active', 'triggered', 'disabled', 'expired']

export function resolveAlertStatus(status: string | null | undefined): AlertStatus | null {
  if (!status) return null

  const normalized = status.trim().toLowerCase()
  if (normalized === 'inactive') return 'disabled'
  if (ALERT_STATUSES.includes(normalized as AlertStatus)) {
    return normalized as AlertStatus
  }

  return null
}

export function isAlertEnabled(status: AlertStatus): boolean {
  return status === 'active' || status === 'triggered'
}

export function toggledAlertStatus(status: AlertStatus): 'active' | 'disabled' {
  return isAlertEnabled(status) ? 'disabled' : 'active'
}

export type AlertListStatusFilter = 'all' | 'active' | 'inactive'

export function matchesAlertStatusFilter(
  status: AlertStatus | string,
  filter: AlertListStatusFilter,
): boolean {
  if (filter === 'all') return true

  const resolved = resolveAlertStatus(status)
  const enabled = resolved ? isAlertEnabled(resolved) : false
  return filter === 'active' ? enabled : !enabled
}
