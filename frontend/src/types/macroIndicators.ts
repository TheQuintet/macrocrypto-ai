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

/** BTC impact of an indicator print. Matches data-service regime visuals. */
export type BtcImpactPolarity = 'positive' | 'negative' | 'neutral'

export type BtcImpact = {
  polarity: BtcImpactPolarity
  toneClass: 'text-positive' | 'text-negative' | 'text-muted-foreground'
  label: 'Positive for BTC' | 'Negative for BTC' | 'Neutral'
  reason: string
}
