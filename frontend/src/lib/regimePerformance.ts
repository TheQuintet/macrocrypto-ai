import type { RegimePerformanceRow } from '@/types/regime'

/**
 * Oldest first.
 *
 * The endpoint returns completed regimes newest-first and then appends the
 * active one, so its order is neither chronological nor reverse — a chart
 * drawn straight from it would put "now" in the middle.
 */
export function sortRegimesByStart(rows: RegimePerformanceRow[]) {
  return [...rows].sort((a, b) => a.startDate.localeCompare(b.startDate))
}

/** Signed percent, or an em dash when the service has no figure. */
export function formatPercent(value: number | null) {
  if (value == null || !Number.isFinite(value)) {
    return '—'
  }

  return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`
}

/** Sharpe and other unitless ratios. */
export function formatRatio(value: number | null) {
  if (value == null || !Number.isFinite(value)) {
    return '—'
  }

  return value.toFixed(2)
}

export function formatRegimePrice(value: number | null) {
  if (value == null || !Number.isFinite(value)) {
    return '—'
  }

  return `$${Math.round(value).toLocaleString('en-US')}`
}

function formatMonth(date: string) {
  const parsed = new Date(`${date}T00:00:00Z`)

  if (Number.isNaN(parsed.getTime())) {
    return date
  }

  return parsed.toLocaleDateString('en-US', {
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  })
}

/** `Aug 2023 – Feb 2024`, or `Mar 2024 – now` while a regime is still open. */
export function formatRegimeRange(startDate: string, endDate: string | null) {
  return `${formatMonth(startDate)} – ${endDate ? formatMonth(endDate) : 'now'}`
}

/** Green above zero, red below — the same reading as the price changes. */
export function returnToneClass(value: number | null) {
  if (value == null || !Number.isFinite(value) || value === 0) {
    return 'text-muted-foreground'
  }

  return value > 0 ? 'text-positive' : 'text-negative'
}
