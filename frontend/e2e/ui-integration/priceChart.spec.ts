import { expect, test } from '@playwright/test'
import { goToRoute } from './routing.specHelpers'
import { MOBILE_VIEWPORT, expectNoHorizontalScroll } from './priceDisplay.specHelpers'
import {
  expectCandleHoverLine,
  expectCandleIntervalSelected,
  expectCandleShapesWellFormed,
  expectCandlesFillPlot,
  expectCandlesRendered,
  expectCandleReadout,
  expectCandleReadoutHint,
  expectNoCandleHoverLine,
  expectOhlcTooltip,
  hoverMiddleCandle,
  movePointerOffChart,
  selectCandleInterval,
} from './priceChart.specHelpers'

test.describe('price chart UI integration', () => {
  test('opens on candlesticks', async ({ page }) => {
    await goToRoute(page, 'dashboard')

    await expectCandlesRendered(page)
    await expectCandleShapesWellFormed(page)
  })

  test('scales candles to fill the plot rather than a sliver', async ({
    page,
  }) => {
    await goToRoute(page, 'dashboard')
    await expectCandlesRendered(page)

    await expectCandlesFillPlot(page)
  })

  test('renders candles on mobile without horizontal scrolling', async ({
    page,
  }) => {
    await page.setViewportSize(MOBILE_VIEWPORT)
    await goToRoute(page, 'dashboard')

    await expectCandlesRendered(page)
    await expectCandleShapesWellFormed(page)
    await expectNoHorizontalScroll(page)
  })

  test('shows candle values under the chart on mobile', async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT)
    await goToRoute(page, 'dashboard')
    await expectCandlesRendered(page)
    await expectCandleReadoutHint(page)

    await hoverMiddleCandle(page)

    await expectCandleReadout(page)
    await expect(page.getByRole('tooltip')).toHaveCount(0)
  })
})

test.describe('candle hover marker UI integration', () => {
  test('marks the hovered candle with a vertical line', async ({ page }) => {
    await goToRoute(page, 'dashboard')
    await expectCandlesRendered(page)

    await hoverMiddleCandle(page)

    await expectCandleHoverLine(page)
  })

  test('clears the marker when the pointer leaves the chart', async ({
    page,
  }) => {
    await goToRoute(page, 'dashboard')
    await expectCandlesRendered(page)
    await hoverMiddleCandle(page)
    await expectCandleHoverLine(page)

    await movePointerOffChart(page)

    await expectNoCandleHoverLine(page)
  })

  test('shows the OHLC tooltip alongside the marker', async ({ page }) => {
    await goToRoute(page, 'dashboard')
    await expectCandlesRendered(page)

    await hoverMiddleCandle(page)

    await expectCandleHoverLine(page)
    await expectOhlcTooltip(page)
  })
})

test.describe('candle interval UI integration', () => {
  test('switches between daily and weekly candles', async ({ page }) => {
    await goToRoute(page, 'dashboard')
    await expectCandlesRendered(page)
    await expectCandleIntervalSelected(page, 'Daily')

    await selectCandleInterval(page, 'Weekly')

    await expectCandleIntervalSelected(page, 'Weekly')
    await expectCandlesRendered(page)
  })
})
