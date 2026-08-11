export function formatPriceTick(value: number) {
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

/** Margins for the panning plot (no left axis). */
export const CHART_PLOT_MARGIN = {
  top: 8,
  right: 8,
  left: 8,
  bottom: 56,
} as const

/** Margins for the fixed Y-axis — match plot top/bottom for tick alignment. */
export const CHART_Y_AXIS_MARGIN = {
  top: 8,
  right: 0,
  left: 0,
  bottom: 56,
} as const
