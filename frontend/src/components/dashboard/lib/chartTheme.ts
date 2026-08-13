/** Match Tailwind `sm` — below this, chart chrome uses compact ticks/margins. */
export const CHART_COMPACT_MAX_WIDTH = 640

export function isChartCompact(width: number) {
  return width > 0 && width < CHART_COMPACT_MAX_WIDTH
}

export function formatPriceTick(value: number, compact = false) {
  if (compact) {
    const abs = Math.abs(value)
    if (abs >= 1_000_000) {
      return `$${(value / 1_000_000).toFixed(1)}M`
    }
    if (abs >= 1_000) {
      return `$${Math.round(value / 1_000)}k`
    }
  }

  return `$${Math.round(value).toLocaleString()}`
}

export function formatPriceTooltip(value: unknown) {
  const price = typeof value === 'number' ? value : Number(value)
  return [`$${price.toLocaleString()}`, 'Price'] as [string, string]
}

export const CHART_TOOLTIP_STYLE = {
  background: 'var(--popover)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  color: 'var(--popover-foreground)',
} as const

export const CHART_Y_AXIS_WIDTH = 56
export const CHART_Y_AXIS_WIDTH_COMPACT = 44

/** Margins for the panning plot (no left axis). */
export const CHART_PLOT_MARGIN = {
  top: 8,
  right: 8,
  left: 8,
  bottom: 56,
} as const

export const CHART_PLOT_MARGIN_COMPACT = {
  top: 8,
  right: 4,
  left: 4,
  bottom: 32,
} as const

/** Margins for the fixed Y-axis — match plot top/bottom for tick alignment. */
export const CHART_Y_AXIS_MARGIN = {
  top: 8,
  right: 0,
  left: 0,
  bottom: 56,
} as const

export const CHART_Y_AXIS_MARGIN_COMPACT = {
  top: 8,
  right: 0,
  left: 0,
  bottom: 32,
} as const

export function chartYAxisWidth(compact: boolean) {
  return compact ? CHART_Y_AXIS_WIDTH_COMPACT : CHART_Y_AXIS_WIDTH
}

export function chartPlotMargin(compact: boolean) {
  return compact ? CHART_PLOT_MARGIN_COMPACT : CHART_PLOT_MARGIN
}

export function chartYAxisMargin(compact: boolean) {
  return compact ? CHART_Y_AXIS_MARGIN_COMPACT : CHART_Y_AXIS_MARGIN
}
