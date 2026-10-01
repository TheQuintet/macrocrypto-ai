import { cleanup } from '@testing-library/react'
import { afterEach, describe, it } from 'vitest'
import {
  expectComparisonTooltipOmits,
  expectComparisonTooltipShows,
  expectNoComparisonTooltip,
  makeComparisonPoint,
  renderComparisonTooltip,
  renderInactiveComparisonTooltip,
} from './PredictionAccuracyComparisonTooltip.testHelpers'

describe('PredictionAccuracyComparisonTooltip', () => {
  afterEach(() => {
    cleanup()
  })

  it('shows both prices and the gap between them', () => {
    renderComparisonTooltip()

    expectComparisonTooltipShows(/14 Sep/)
    expectComparisonTooltipShows('Predicted$64,101')
    expectComparisonTooltipShows('Actual$63,880')
    expectComparisonTooltipShows('Gap+$220 (+0.34%)')
  })

  it('names the market the forecast was scored in', () => {
    renderComparisonTooltip()

    expectComparisonTooltipShows('Bull market')
  })

  it('leaves the market out when the service did not classify it', () => {
    renderComparisonTooltip(makeComparisonPoint({ marketCondition: null }))

    expectComparisonTooltipOmits(/market/i)
  })

  it('renders nothing while the cursor is off the plot', () => {
    renderInactiveComparisonTooltip()

    expectNoComparisonTooltip()
  })
})
