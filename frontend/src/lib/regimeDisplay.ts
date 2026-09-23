import type {
  RegimeConfidenceBand,
  RegimeConfidenceDisplay,
  RegimeDisplay,
  RegimeType,
  RegimeVisualIndicator,
} from '@/types/regime'

/**
 * Why each class gets identified, in the same voice as the indicator tooltips.
 *
 * The service classifies from the latest FRED prints and stores only the
 * label, so the reasoning copy lives here — the same way `indicatorBtcImpact`
 * carries the BTC-impact reasons rather than expecting them on the wire.
 */
const REGIME_COPY: Record<RegimeType, { label: string; explanation: string }> =
  {
    high_inflation: {
      label: 'High inflation',
      explanation:
        'CPI is running above the service’s inflation threshold — tighter policy ahead, historically a headwind for BTC.',
    },
    low_inflation: {
      label: 'Low inflation',
      explanation:
        'CPI is running below the service’s inflation threshold — less pressure to tighten, historically a tailwind for BTC.',
    },
    rising_rates: {
      label: 'Rising rates',
      explanation:
        'The federal funds rate has been trending up — tighter liquidity, historically a headwind for BTC.',
    },
    falling_rates: {
      label: 'Falling rates',
      explanation:
        'The federal funds rate has been trending down — easier liquidity, historically a tailwind for BTC.',
    },
    recession: {
      label: 'Recession',
      explanation:
        'GDP growth has turned negative — risk-off conditions, and the weakest backdrop for BTC in this model.',
    },
    growth: {
      label: 'Growth',
      explanation:
        'GDP is expanding — risk-on conditions, historically a tailwind for BTC.',
    },
  }

const STANCE_BY_INDICATOR: Record<
  RegimeVisualIndicator,
  Pick<RegimeDisplay, 'stance' | 'stanceLabel' | 'toneClass'>
> = {
  bull: {
    stance: 'bullish',
    stanceLabel: 'Bull',
    toneClass: 'text-positive',
  },
  bear: {
    stance: 'bearish',
    stanceLabel: 'Bear',
    toneClass: 'text-negative',
  },
  recession: {
    stance: 'bearish',
    stanceLabel: 'Recession',
    toneClass: 'text-negative',
  },
  neutral: {
    stance: 'neutral',
    stanceLabel: 'Neutral',
    toneClass: 'text-warning',
  },
}

/** At or above this, the classifier is sure enough to read as green. */
export const HIGH_CONFIDENCE_MIN = 70

/** Below this, the read is too weak to trust — red. Between here and high is amber. */
export const MODERATE_CONFIDENCE_MIN = 50

export const CONFIDENCE_BAND_ORDER: RegimeConfidenceBand[] = [
  'low',
  'moderate',
  'high',
]

const TONE_BY_BAND: Record<
  RegimeConfidenceBand,
  Pick<RegimeConfidenceDisplay, 'toneClass' | 'barClass'>
> = {
  low: { toneClass: 'text-negative', barClass: 'bg-negative' },
  moderate: { toneClass: 'text-warning', barClass: 'bg-warning' },
  high: { toneClass: 'text-positive', barClass: 'bg-positive' },
}

function isRegimeType(value: string): value is RegimeType {
  // `hasOwn`, not `in` — `in` also matches inherited keys, so a wire value of
  // `toString` would resolve to a function and spread into an empty display.
  return Object.hasOwn(REGIME_COPY, value)
}

/** `high_inflation` -> `High inflation`, for a class this build does not know. */
function humanizeRegimeType(regimeType: string) {
  const spaced = regimeType.replace(/_/g, ' ').trim()

  if (!spaced) {
    return 'Unclassified'
  }

  return spaced.charAt(0).toUpperCase() + spaced.slice(1)
}

/** Narrow a wire value, defaulting to the service's own unmapped fallback. */
export function toRegimeVisualIndicator(value: string): RegimeVisualIndicator {
  return Object.hasOwn(STANCE_BY_INDICATOR, value)
    ? (value as RegimeVisualIndicator)
    : 'neutral'
}

/**
 * Label, reasoning, and colour for a regime.
 *
 * The stance comes from the service's `visual_indicator` rather than being
 * re-derived here — the backend owns that call, and two mappings would drift.
 */
export function regimeDisplay(
  regimeType: string,
  visualIndicator: RegimeVisualIndicator,
): RegimeDisplay {
  const copy = isRegimeType(regimeType)
    ? REGIME_COPY[regimeType]
    : {
        label: humanizeRegimeType(regimeType),
        explanation:
          'Classified by the data service from the latest macro indicator prints.',
      }

  return { ...copy, ...STANCE_BY_INDICATOR[visualIndicator] }
}

/** Clamp to the 0–100 the service's own check constraint guarantees. */
export function clampConfidence(confidence: number) {
  if (!Number.isFinite(confidence)) {
    return 0
  }

  return Math.min(100, Math.max(0, confidence))
}

export function formatConfidence(confidence: number) {
  return `${Math.round(clampConfidence(confidence))}%`
}

/**
 * Colour the confidence figure by how sure the classifier is, not by
 * bull / bear. A high-confidence bearish regime is still a strong read.
 */
export function confidenceDisplay(confidence: number): RegimeConfidenceDisplay {
  const value = clampConfidence(confidence)

  if (value >= HIGH_CONFIDENCE_MIN) {
    return { band: 'high', ...TONE_BY_BAND.high }
  }

  if (value >= MODERATE_CONFIDENCE_MIN) {
    return { band: 'moderate', ...TONE_BY_BAND.moderate }
  }

  return { band: 'low', ...TONE_BY_BAND.low }
}

export function formatConfidenceBand(band: RegimeConfidenceBand) {
  switch (band) {
    case 'high':
      return 'High'
    case 'moderate':
      return 'Moderate'
    case 'low':
      return 'Low'
  }
}

export function formatConfidenceBandRange(band: RegimeConfidenceBand) {
  switch (band) {
    case 'high':
      return `≥${HIGH_CONFIDENCE_MIN}%`
    case 'moderate':
      return `${MODERATE_CONFIDENCE_MIN}–${HIGH_CONFIDENCE_MIN - 1}%`
    case 'low':
      return `<${MODERATE_CONFIDENCE_MIN}%`
  }
}

export function confidenceBandTone(band: RegimeConfidenceBand) {
  return TONE_BY_BAND[band]
}

/**
 * When the classification was made, in UTC.
 *
 * 24-hour so it reads as a timestamp rather than a time of day, and one
 * string rather than an interpolated fragment so the whole line is legible
 * to a screen reader in order.
 */
export function formatRegimeIdentifiedAt(identifiedAt: string) {
  const identified = new Date(identifiedAt)

  if (Number.isNaN(identified.getTime())) {
    return 'an unknown time'
  }

  const stamp = identified.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
    timeZone: 'UTC',
  })

  return `${stamp} UTC`
}
