import { cleanup } from '@testing-library/react'
import { afterEach, describe, it } from 'vitest'
import {
  expectTrendTooltipShows,
  renderTrendTooltip,
} from './PredictionAccuracyTrendTooltip.testHelpers'

describe('PredictionAccuracyTrendTooltip', () => {
  afterEach(() => {
    cleanup()
  })

  it("shows each horizon's accuracy on the hovered day", () => {
    renderTrendTooltip()

    expectTrendTooltipShows(/14 Sep/)
    expectTrendTooltipShows('24h forecasts98%')
    expectTrendTooltipShows('7d forecasts89%')
  })

  it('marks a day one horizon was not scored', () => {
    renderTrendTooltip({ '7d': null })

    expectTrendTooltipShows('7d forecasts--')
  })
})
