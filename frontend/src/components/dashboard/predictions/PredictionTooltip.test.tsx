import { cleanup } from '@testing-library/react'
import { afterEach, describe, it } from 'vitest'
import {
  expectNoTooltip,
  expectTooltipMissing,
  expectTooltipShows,
  makeForecastRow,
  makeHistoryRow,
  renderTooltip,
  renderTooltipWithoutPoint,
} from './PredictionTooltip.testHelpers'

describe('PredictionTooltip', () => {
  afterEach(() => {
    cleanup()
  })

  it('shows the point time, forecast, and both bounds', () => {
    renderTooltip()

    expectTooltipShows(/15 Jun/)
    expectTooltipShows('$64,000.00')
    expectTooltipShows('$64,600.00')
    expectTooltipShows('$63,400.00')
  })

  it('shows the range width and the confidence it was computed at', () => {
    renderTooltip({ confidence: 0.95 })

    expectTooltipShows('$1,200.00')
    expectTooltipShows('95% confidence')
  })

  it('measures the point against the current price', () => {
    renderTooltip({
      row: makeForecastRow({ predicted: 64_135 }),
      currentPrice: 63_500,
    })

    expectTooltipShows('+1.00%')
  })

  it('omits the comparison when the batch has no current price', () => {
    renderTooltip({ currentPrice: null })

    expectTooltipShows('$64,000.00')
    expectTooltipMissing('vs current')
  })

  it('shows OHLC detail for a candle on the history half', () => {
    renderTooltip({ row: makeHistoryRow() })

    expectTooltipShows('Open')
    expectTooltipShows('High')
    expectTooltipShows('Low')
    expectTooltipShows('Close')
    expectTooltipShows('$63,800.00')
  })

  it('does not offer forecast bounds for a historical candle', () => {
    renderTooltip({ row: makeHistoryRow() })

    expectTooltipMissing('Upper bound')
    expectTooltipMissing(/confidence/)
  })

  it('reports a fitted value without inventing bounds it has none of', () => {
    renderTooltip({
      row: makeHistoryRow({
        open: undefined,
        high: undefined,
        low: undefined,
        close: undefined,
        candle: undefined,
        fit: 63_250,
      }),
    })

    expectTooltipShows('Model fit')
    expectTooltipShows('$63,250.00')
    expectTooltipMissing('Upper bound')
    expectTooltipMissing('$0.00')
  })

  it('renders nothing when the pointer is off the chart', () => {
    renderTooltip({ active: false })

    expectNoTooltip()
  })

  it('renders nothing when no point is under the cursor', () => {
    renderTooltipWithoutPoint()

    expectNoTooltip()
  })
})
