import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { usePredictionStore } from '@/stores/predictionStore'
import { resetPredictionStore } from '@/stores/predictionStore.testHelpers'
import {
  CONFIDENCE_GROUP,
  HORIZON_GROUP,
  expectConfidenceSelected,
  expectHorizonSelected,
  expectOptionsOffered,
  renderPredictionControls,
  selectConfidence,
  selectHorizon,
} from './PredictionControls.testHelpers'

describe('prediction view controls', () => {
  beforeEach(() => {
    resetPredictionStore()
  })

  afterEach(() => {
    cleanup()
  })

  it('opens on the 24h horizon at 85% confidence', () => {
    renderPredictionControls()

    expectHorizonSelected('24h')
    expectConfidenceSelected('85%')
  })

  it('offers both horizons and all three confidence levels', () => {
    renderPredictionControls()

    expectOptionsOffered(HORIZON_GROUP, ['24h', '7d'])
    expectOptionsOffered(CONFIDENCE_GROUP, ['70%', '85%', '95%'])
  })

  it('switches the whole screen to the 7d window', async () => {
    renderPredictionControls()

    await selectHorizon('7d')

    expectHorizonSelected('7d')
    expect(usePredictionStore.getState().horizon).toBe('7d')
  })

  it('changes the confidence level the bounds are computed at', async () => {
    renderPredictionControls()

    await selectConfidence('95%')

    expectConfidenceSelected('95%')
    expect(usePredictionStore.getState().confidence).toBe(0.95)
  })

  it('keeps the horizon when only the confidence changes', async () => {
    renderPredictionControls()
    await selectHorizon('7d')

    await selectConfidence('70%')

    expectHorizonSelected('7d')
    expectConfidenceSelected('70%')
  })
})
