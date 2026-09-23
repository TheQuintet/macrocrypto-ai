import { describe, expect, it } from 'vitest'
import {
  HIGH_PREDICTION_CONFIDENCE,
  MODERATE_PREDICTION_CONFIDENCE,
  clampPredictionConfidence,
  formatPredictionConfidenceBand,
  formatPredictionConfidenceBandRange,
  predictionConfidenceDisplay,
  predictionConfidencePercent,
} from '@/components/dashboard/lib/predictionConfidence'

describe('predictionConfidence', () => {
  it('clamps the wire float to 0–1', () => {
    expect(clampPredictionConfidence(1.4)).toBe(1)
    expect(clampPredictionConfidence(-0.2)).toBe(0)
    expect(clampPredictionConfidence(Number.NaN)).toBe(0)
  })

  it('reads the wire float as a whole percent', () => {
    expect(predictionConfidencePercent(0.7)).toBe(70)
    expect(predictionConfidencePercent(0.85)).toBe(85)
    expect(predictionConfidencePercent(0.95)).toBe(95)
  })

  it('names 70% low, 85% moderate, and 95% high', () => {
    expect(predictionConfidenceDisplay(0.7)).toMatchObject({
      band: 'low',
      toneClass: 'text-negative',
    })
    expect(predictionConfidenceDisplay(MODERATE_PREDICTION_CONFIDENCE)).toMatchObject({
      band: 'moderate',
      toneClass: 'text-warning',
    })
    expect(predictionConfidenceDisplay(HIGH_PREDICTION_CONFIDENCE)).toMatchObject({
      band: 'high',
      toneClass: 'text-positive',
    })
  })

  it('keeps values just under the next interval in the lower band', () => {
    expect(predictionConfidenceDisplay(0.849).band).toBe('low')
    expect(predictionConfidenceDisplay(0.949).band).toBe('moderate')
  })

  it('labels each band with the interval it stands for', () => {
    expect(formatPredictionConfidenceBand('low')).toBe('Low')
    expect(formatPredictionConfidenceBandRange('low')).toBe('70%')
    expect(formatPredictionConfidenceBandRange('moderate')).toBe('85%')
    expect(formatPredictionConfidenceBandRange('high')).toBe('95%')
  })
})
