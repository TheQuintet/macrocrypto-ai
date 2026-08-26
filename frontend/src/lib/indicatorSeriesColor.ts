/** Canonical series colors live in `src/index.css` as `--indicator-*` tokens. */
const INDICATOR_SERIES_COLOR: Record<string, string> = {
  cpi: 'var(--indicator-cpi)',
  federal_funds_rate: 'var(--indicator-federal-funds-rate)',
  gdp: 'var(--indicator-gdp)',
}

const FALLBACK_SERIES_COLOR = 'var(--muted-foreground)'

export function indicatorSeriesColor(name: string): string {
  return INDICATOR_SERIES_COLOR[name.toLowerCase()] ?? FALLBACK_SERIES_COLOR
}
