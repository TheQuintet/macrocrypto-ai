/**
 * Regime classes data-service persists — the `ck_current_regime_type`
 * constraint on `current_regime`.
 */
export type RegimeType =
  | 'high_inflation'
  | 'low_inflation'
  | 'rising_rates'
  | 'falling_rates'
  | 'recession'
  | 'growth'

/**
 * Market stance the service attaches to a regime (`REGIME_VISUAL_INDICATORS`).
 *
 * The table constraint allows only bull / bear / recession, but
 * `get_visual_indicator` falls back to `'neutral'` for an unmapped regime, so
 * the UI accepts it rather than rendering a blank card if that ever ships.
 */
export type RegimeVisualIndicator = 'bull' | 'bear' | 'recession' | 'neutral'

/** Live API vs frontend stand-in — set by the fetcher, not the UI. */
export type RegimeSource = 'live' | 'simulated'

/** GET /api/v1/regimes/current, in the service's own wire shape. */
export type CurrentRegimeResponse = {
  id: number
  regime_type: string
  confidence: number
  visual_indicator: string
  identified_at: string
  expires_at: string | null
}

export type CurrentRegime = {
  source: RegimeSource
  id: number
  /**
   * Left as `string`: an unrecognised class from a newer backend should still
   * render, not break the card. `regimeDisplay` decides how it reads.
   */
  regimeType: string
  /** Percentage, 0–100, as the service stores it. */
  confidence: number
  visualIndicator: RegimeVisualIndicator
  identifiedAt: string
  expiresAt: string | null
}

/** Green / red / amber, matching the indicator cards' BTC-impact colours. */
export type RegimeStance = 'bullish' | 'bearish' | 'neutral'

export type RegimeToneClass =
  | 'text-positive'
  | 'text-negative'
  | 'text-warning'

export type RegimeBarClass = 'bg-positive' | 'bg-negative' | 'bg-warning'

/** How sure the classifier is — independent of bull / bear / recession. */
export type RegimeConfidenceBand = 'high' | 'moderate' | 'low'

export type RegimeConfidenceDisplay = {
  band: RegimeConfidenceBand
  toneClass: RegimeToneClass
  barClass: RegimeBarClass
}

/** How a regime reads on screen: what it is called, why, and its colour. */
export type RegimeDisplay = {
  label: string
  /** One line on what the classification is based on. */
  explanation: string
  stance: RegimeStance
  /** Badge text for the visual indicator — Bull / Bear / Recession. */
  stanceLabel: string
  toneClass: RegimeToneClass
}

/** Whether a regime has ended, or is the one we are currently in. */
export type RegimeStatus = 'completed' | 'active'

/** BTC performance during a regime — every field optional on the wire. */
export type RegimePerformanceMetricsResponse = {
  avg_return: number | null
  max_drawdown: number | null
  volatility: number | null
  sharpe_ratio: number | null
  btc_price_start: number | null
  btc_price_end: number | null
}

/** One row of GET /api/v1/regimes/performance. */
export type RegimePerformanceRowResponse = {
  regime_id: number
  regime_type: string
  start_date: string
  end_date: string | null
  status: string
  performance: RegimePerformanceMetricsResponse
}

export type RegimePerformanceMetrics = {
  avgReturn: number | null
  maxDrawdown: number | null
  volatility: number | null
  sharpeRatio: number | null
  btcPriceStart: number | null
  btcPriceEnd: number | null
}

export type RegimePerformanceRow = {
  regimeId: number
  regimeType: string
  startDate: string
  endDate: string | null
  status: RegimeStatus
  performance: RegimePerformanceMetrics
}

export type RegimePerformance = {
  source: RegimeSource
  rows: RegimePerformanceRow[]
}

/** One regime in GET /api/v1/regimes (history), newest first on the wire. */
export type RegimeHistoryRowResponse = {
  id: number
  regime_type: string
  start_date: string
  end_date: string | null
  performance: RegimePerformanceMetricsResponse | null
}

export type RegimeHistoryRow = {
  id: number
  regimeType: string
  startDate: string
  endDate: string | null
  /** Open-ended regime — the one we are currently in. */
  isCurrent: boolean
  performance: RegimePerformanceMetrics | null
}

export type RegimeHistory = {
  source: RegimeSource
  rows: RegimeHistoryRow[]
}

/** One regime positioned on the timeline band, as percentages of its width. */
export type RegimeTimelineSegment = {
  row: RegimeHistoryRow
  /** Distance from the left edge of the band, 0–100. */
  offsetPercent: number
  /** Share of the band this regime covers, 0–100. */
  widthPercent: number
  startMs: number
  endMs: number
}

/** BTC over a similar historical window, when history reaches back that far. */
export type SimilarPeriodBtcResponse = {
  price_start: number
  price_end: number
  return_percent: number
  observations: number
}

export type SimilarPeriodMatchingIndicatorResponse = {
  indicator: string
  normalized_difference: number
}

/** One entry of GET /api/v1/regimes/history/similar-periods. */
export type SimilarPeriodResponse = {
  period_start: string
  period_end: string
  distance: number
  similarity_score: number
  reason: string
  matching_indicators: SimilarPeriodMatchingIndicatorResponse[]
  macro_conditions: Record<string, number>
  btc_performance: SimilarPeriodBtcResponse | null
}

export type SimilarPeriodsApiResponse = {
  current_conditions: Record<string, number>
  method: string
  period_count: number
  similar_periods: SimilarPeriodResponse[]
  message?: string | null
}

export type SimilarPeriodBtc = {
  priceStart: number
  priceEnd: number
  returnPercent: number
  observations: number
}

export type SimilarPeriodMatchingIndicator = {
  indicator: string
  normalizedDifference: number
}

export type SimilarPeriod = {
  /** Stable key for lists — the service does not send an id. */
  id: string
  periodStart: string
  periodEnd: string
  distance: number
  /** 0–100 confidence in the match. */
  similarityScore: number
  reason: string
  matchingIndicators: SimilarPeriodMatchingIndicator[]
  macroConditions: Record<string, number>
  btcPerformance: SimilarPeriodBtc | null
}

export type SimilarPeriods = {
  source: RegimeSource
  /** How the service found these — shown so the reader can judge them. */
  method: string
  currentConditions: Record<string, number>
  periods: SimilarPeriod[]
  message: string | null
}

/** One pane on the regime analysis page. */
export type RegimePageView = 'performance' | 'timeline' | 'similarPeriods'

/**
 * Indicators the similar-period engine compares — data-service
 * `SimilarPeriodService.INDICATORS`.
 */
export type SimilarPeriodIndicatorName =
  | 'cpi'
  | 'federal_funds_rate'
  | 'm2_money_supply'
  | 'dxy'
  | 'ten_year_treasury'
  | 'gdp'
  | 'unemployment'
