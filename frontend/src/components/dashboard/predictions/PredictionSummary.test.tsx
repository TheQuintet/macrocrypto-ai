import { cleanup, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import {
  expectBandWidth,
  expectPredictedPriceTone,
  expectKeyLevels,
  expectStat,
  expectTrend,
  makePredictionPoint,
  renderSummary,
} from './PredictionSummary.testHelpers'

describe('PredictionSummary', () => {
  afterEach(() => {
    cleanup()
  })

  it('reports the current price, expected change, and confidence level', () => {
    renderSummary()

    expectStat('Current price', '$63,500.00')
    expectStat('Expected change', '+1.10%')
    expectStat('Confidence', '85%')
  })

  it('shows the trend direction the model returned', () => {
    renderSummary({ trend: 'down', priceChangePct: -2.4 })

    expectTrend('Down')
    expectStat('Expected change', '-2.40%')
  })

  it('reads a flat forecast as neutral', () => {
    renderSummary({ trend: 'neutral', priceChangePct: 0.1 })

    expectTrend('Neutral')
  })

  it('derives the key levels from the widest bounds in the batch', () => {
    renderSummary()

    expectKeyLevels('$64,900.00', '$63,400.00')
  })

  it('prints each bound once rather than repeating the range', () => {
    renderSummary()

    expect(screen.getAllByText('$64,900.00')).toHaveLength(1)
    expect(screen.getAllByText('$63,400.00')).toHaveLength(1)
  })

  it('colours the headline forecast by direction', () => {
    renderSummary({ predictedEndPrice: 64_200, priceChangePct: 1.1 })

    expectPredictedPriceTone('$64,200.00', 'text-positive')
  })

  it('colours a downward forecast red', () => {
    renderSummary({
      trend: 'down',
      predictedEndPrice: 62_800,
      priceChangePct: -1.1,
    })

    expectPredictedPriceTone('$62,800.00', 'text-negative')
  })

  it('leaves a flat forecast untinted', () => {
    renderSummary({
      trend: 'neutral',
      predictedEndPrice: 63_900,
      priceChangePct: 0,
    })

    expectPredictedPriceTone('$63,900.00', 'text-muted-foreground')
  })

  it('labels the key levels by the horizon they were forecast over', () => {
    const { container } = renderSummary({ horizon: '7d' })

    expect(container.textContent).toContain('Widest daily bounds')
    expect(container.textContent).toContain('Predicted in 7 days')
  })

  it('reads a tight band as a narrow, higher-certainty range', () => {
    renderSummary({
      points: [
        makePredictionPoint({
          predictedPrice: 64_000,
          lowerBound: 63_840,
          upperBound: 64_160,
        }),
      ],
    })

    expectBandWidth('Narrow')
  })

  it('reads a broad band as a wide, lower-certainty range', () => {
    renderSummary({
      points: [
        makePredictionPoint({
          predictedPrice: 64_000,
          lowerBound: 61_000,
          upperBound: 67_000,
        }),
      ],
    })

    expectBandWidth('Wide')
  })

  it('shows a placeholder rather than a made-up baseline with no current price', () => {
    renderSummary({ currentPrice: null, priceChangePct: null })

    expectStat('Current price', '--')
    expectStat('Expected change', '--')
  })
})
