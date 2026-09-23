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
