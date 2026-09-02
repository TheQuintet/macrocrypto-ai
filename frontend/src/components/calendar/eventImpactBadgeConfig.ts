import type { EventImpactLevel } from '@/types/economicCalendar'

export type EventImpactBadgeConfig = {
  label: string
  shortLabel: string
  className: string
  dot: string
}

/**
 * Impact styling, in the same shape as the price-alert status badge so the two
 * alert surfaces read as one system.
 */
const impactConfig: Record<EventImpactLevel, EventImpactBadgeConfig> = {
  high: {
    label: 'High impact',
    shortLabel: 'High',
    className:
      'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    dot: 'bg-red-500',
  },
  medium: {
    label: 'Medium impact',
    shortLabel: 'Medium',
    className:
      'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    dot: 'bg-yellow-500',
  },
  low: {
    label: 'Low impact',
    shortLabel: 'Low',
    className:
      'bg-gray-100 text-gray-700 dark:bg-gray-800/50 dark:text-gray-400',
    dot: 'bg-gray-500',
  },
}

const unknownConfig: EventImpactBadgeConfig = {
  label: 'Unknown impact',
  shortLabel: 'Unknown',
  className: 'bg-muted text-muted-foreground',
  dot: 'bg-muted-foreground',
}

/** Falls back to a neutral badge for an impact level the feed invented. */
export function getEventImpactBadgeConfig(
  impact: EventImpactLevel | string,
): EventImpactBadgeConfig {
  return impactConfig[impact as EventImpactLevel] ?? unknownConfig
}
