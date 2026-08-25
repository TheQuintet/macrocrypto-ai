import type { MacroIndicator, MacroIndicatorSeries } from '@/types/macroIndicators'

export function formatIndicatorTitle(name: string) {
  return name.replace(/_/g, ' ')
}

export function formatIndicatorTimestamp(timeString: string) {
  return new Date(timeString).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'UTC',
  })
}

export function formatIndicatorChartLabel(timeString: string) {
  return new Date(timeString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: '2-digit',
    timeZone: 'UTC',
  })
}

/** Group mixed API rows into per-indicator series, oldest → newest. */
export function groupIndicatorsByName(
  indicators: MacroIndicator[],
): MacroIndicatorSeries[] {
  const grouped = new Map<string, MacroIndicator[]>()

  for (const indicator of indicators) {
    const key = indicator.indicator_name
    const existing = grouped.get(key)
    if (existing) {
      existing.push(indicator)
    } else {
      grouped.set(key, [indicator])
    }
  }

  return [...grouped.entries()].map(([name, points]) => {
    const sorted = [...points].sort(
      (left, right) => Date.parse(left.time) - Date.parse(right.time),
    )
    return {
      name,
      points: sorted,
      latest: sorted[sorted.length - 1],
    }
  })
}
