import type { AlertStatus } from '@/types/alerts/priceAlert'
import { resolveAlertStatus } from './alertStatus'

export type AlertStatusBadgeConfig = {
  label: string
  className: string
  dot: string
}

const statusConfig: Record<AlertStatus, AlertStatusBadgeConfig> = {
  active: {
    label: 'Active',
    className: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    dot: 'bg-green-500',
  },
  triggered: {
    label: 'Triggered',
    className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    dot: 'bg-blue-500',
  },
  disabled: {
    label: 'Inactive',
    className: 'bg-gray-100 text-gray-700 dark:bg-gray-800/50 dark:text-gray-400',
    dot: 'bg-gray-500',
  },
  expired: {
    label: 'Expired',
    className: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    dot: 'bg-yellow-500',
  },
}

const unknownConfig: AlertStatusBadgeConfig = {
  label: 'Unknown',
  className: 'bg-muted text-muted-foreground',
  dot: 'bg-muted-foreground',
}

export function getAlertStatusBadgeConfig(status: AlertStatus | string): AlertStatusBadgeConfig {
  const resolved = resolveAlertStatus(status)
  return resolved ? statusConfig[resolved] : unknownConfig
}
