import { cleanup } from '@testing-library/react'
import { afterEach, describe, it } from 'vitest'
import {
  expectCoverageLevelSelected,
  expectNoGradedTone,
  expectPredictionConfidenceScaleKey,
  renderPredictionConfidenceScale,
} from '@/components/dashboard/predictions/PredictionConfidenceScale.testHelpers'

describe('PredictionConfidenceScale', () => {
  afterEach(() => {
    cleanup()
  })

  it('lists every coverage level on offer', () => {
    renderPredictionConfidenceScale()
    expectPredictionConfidenceScaleKey()
  })

  it('picks out the selected level', () => {
    renderPredictionConfidenceScale(0.95)
    expectCoverageLevelSelected('95%')
  })

  it('styles no level as better than another', () => {
    renderPredictionConfidenceScale(0.7)
    expectNoGradedTone()
  })
})
