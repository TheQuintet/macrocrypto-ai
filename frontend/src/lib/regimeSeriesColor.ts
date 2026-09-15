/** Canonical regime colors live in `src/index.css` as `--regime-*` tokens. */
const REGIME_SERIES_COLOR: Record<string, string> = {
  growth: 'var(--regime-growth)',
  low_inflation: 'var(--regime-low-inflation)',
  falling_rates: 'var(--regime-falling-rates)',
  rising_rates: 'var(--regime-rising-rates)',
  high_inflation: 'var(--regime-high-inflation)',
  recession: 'var(--regime-recession)',
}

const FALLBACK_SERIES_COLOR = 'var(--muted-foreground)'

export function regimeSeriesColor(regimeType: string): string {
  return (
    REGIME_SERIES_COLOR[regimeType.toLowerCase()] ?? FALLBACK_SERIES_COLOR
  )
}
