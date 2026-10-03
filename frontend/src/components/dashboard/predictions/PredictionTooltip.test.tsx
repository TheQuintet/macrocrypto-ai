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

  it('labels every model value as a prediction — there is no fit', () => {
    renderTooltip()

    expectTooltipShows('Predicted')
    expectTooltipMissing('Model fit')
  })

  /** An older batch has forecast hours that have since traded. */
  it('shows the actual close beside a forecast hour that has traded', () => {
    renderTooltip({ row: makeForecastRow({ close: 63_950 }) })

    expectTooltipShows('Actual close')
    expectTooltipShows('$63,950.00')
    expectTooltipShows('Upper bound')
  })

  it('leaves the actual close off a forecast hour still ahead', () => {
    renderTooltip()

    expectTooltipMissing('Actual close')
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
