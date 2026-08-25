/** Latest observation from GET /api/v1/indicators. */
export type MacroIndicator = {
  indicator_name: string
  time: string
  current_value: number
  previous_value: number | null
  change_percent: number | null
  trend: '↑' | '↓' | '→'
  source: string
}

/** `period` query on GET /api/v1/indicators — omit for latest. */
export type MacroIndicatorPeriod = '30d' | '90d' | '1y' | '5y'

export type MacroIndicatorView = 'current' | 'historical'

export type MacroIndicatorSeries = {
  name: string
  points: MacroIndicator[]
  latest: MacroIndicator
}

/** BTC impact of an indicator print. Matches data-service regime visuals. */
export type BtcImpactPolarity = 'positive' | 'negative' | 'neutral'

export type BtcImpact = {
  polarity: BtcImpactPolarity
  toneClass: 'text-positive' | 'text-negative' | 'text-muted-foreground'
  label: 'Positive for BTC' | 'Negative for BTC' | 'Neutral'
  reason: string
}
