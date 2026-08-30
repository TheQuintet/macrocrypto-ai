/**
 * Where indicator values came from. Simulated data must be labelled in the UI
 * the same way BTC snapshots use `PriceSource`.
 */
export type MacroIndicatorDataSource = 'live' | 'simulated'

/** Latest observation from GET /api/v1/indicators. */
export type MacroIndicator = {
  indicator_name: string
  time: string
  current_value: number
  previous_value: number | null
  change_percent: number | null
  trend: '↑' | '↓' | '→'
  /** Data vendor on the wire, e.g. `fred`. */
  source: string
  /** Live API vs frontend stand-in — set by the fetcher, not the UI. */
  dataSource: MacroIndicatorDataSource
}

/** Backend `period` query on GET /api/v1/indicators. */
export type MacroIndicatorApiPeriod = '30d' | '90d' | '1y' | '5y'

/** Names shown in the history chart, table, and series filter. */
export type MainIndicatorName = 'cpi' | 'federal_funds_rate' | 'gdp'

/** `'all'` shows every series; otherwise only that indicator. */
export type IndicatorHistoryFilter = 'all' | MainIndicatorName

export type MacroIndicatorSeries = {
  name: string
  points: MacroIndicator[]
  latest: MacroIndicator
}

/** One aligned timestamp for the combined history chart (series keys are indexed to 100). */
export type IndexedIndicatorChartRow = {
  time: string
  timeMs: number
  values: Record<string, number>
  /** Raw as-of prints when the row is aligned to a BTC candle. */
  prints?: Record<string, number>
}

/** BTC impact of an indicator print. Matches data-service regime visuals. */
export type BtcImpactPolarity = 'positive' | 'negative' | 'neutral'

export type BtcImpact = {
  polarity: BtcImpactPolarity
  toneClass: 'text-positive' | 'text-negative' | 'text-muted-foreground'
  label: 'Positive for BTC' | 'Negative for BTC' | 'Neutral'
  reason: string
}
