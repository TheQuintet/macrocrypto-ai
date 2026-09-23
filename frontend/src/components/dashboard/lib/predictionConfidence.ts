import type {
  PredictionConfidenceBand,
  PredictionConfidenceDisplay,
} from '@/types/predictions'

/** The three intervals the endpoint computes bounds at, named for a glance. */
export const HIGH_PREDICTION_CONFIDENCE = 0.95
export const MODERATE_PREDICTION_CONFIDENCE = 0.85

export const PREDICTION_CONFIDENCE_BAND_ORDER: PredictionConfidenceBand[] = [
  'low',
  'moderate',
  'high',
]

const TONE_BY_BAND: Record<
  PredictionConfidenceBand,
  Pick<PredictionConfidenceDisplay, 'toneClass' | 'barClass'>
> = {
  low: { toneClass: 'text-negative', barClass: 'bg-negative' },
  moderate: { toneClass: 'text-warning', barClass: 'bg-warning' },
  high: { toneClass: 'text-positive', barClass: 'bg-positive' },
}

export function clampPredictionConfidence(confidence: number) {
  if (!Number.isFinite(confidence)) {
    return 0
  }

  return Math.min(1, Math.max(0, confidence))
}

export function predictionConfidencePercent(confidence: number) {
  return Math.round(clampPredictionConfidence(confidence) * 100)
}

export function predictionConfidenceDisplay(
  confidence: number,
): PredictionConfidenceDisplay {
  const value = clampPredictionConfidence(confidence)

  if (value >= HIGH_PREDICTION_CONFIDENCE) {
    return { band: 'high', ...TONE_BY_BAND.high }
  }

  if (value >= MODERATE_PREDICTION_CONFIDENCE) {
    return { band: 'moderate', ...TONE_BY_BAND.moderate }
  }

  return { band: 'low', ...TONE_BY_BAND.low }
}

export function formatPredictionConfidenceBand(band: PredictionConfidenceBand) {
  switch (band) {
    case 'high':
      return 'High'
    case 'moderate':
      return 'Moderate'
    case 'low':
      return 'Low'
  }
}

export function formatPredictionConfidenceBandRange(
  band: PredictionConfidenceBand,
) {
  switch (band) {
    case 'high':
      return '95%'
    case 'moderate':
      return '85%'
    case 'low':
      return '70%'
  }
}

export function predictionConfidenceBandTone(band: PredictionConfidenceBand) {
  return TONE_BY_BAND[band]
}
