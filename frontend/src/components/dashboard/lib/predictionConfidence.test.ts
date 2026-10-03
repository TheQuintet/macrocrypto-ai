import { describe, expect, it } from 'vitest'
import {
  clampPredictionConfidence,
  describePredictionCoverage,
  formatPredictionCoverage,
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

  it('labels the level as the range it covers, not as a grade', () => {
    expect(formatPredictionCoverage(0.7)).toBe('70% range')
    expect(formatPredictionCoverage(0.95)).toBe('95% range')
  })

  it('says what the coverage level promises', () => {
    expect(describePredictionCoverage(0.85)).toBe(
      'Price expected inside the band 85% of the time',
    )
  })
})
