import { cleanup } from '@testing-library/react'
import { afterEach, describe, it } from 'vitest'
import {
  expectPredictionConfidenceScaleKey,
  renderPredictionConfidenceScale,
} from '@/components/dashboard/predictions/PredictionConfidenceScale.testHelpers'

describe('PredictionConfidenceScale', () => {
  afterEach(() => {
    cleanup()
  })

  it('shows low, moderate, and high with their intervals', () => {
    renderPredictionConfidenceScale()
    expectPredictionConfidenceScaleKey()
  })
})
