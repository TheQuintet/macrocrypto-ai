import { test } from '@playwright/test'
import { goToRoute } from './routing.specHelpers'
import { MOBILE_VIEWPORT, expectNoHorizontalScroll } from './priceDisplay.specHelpers'
import {
  expectCandleHoverLine,
  expectCandleShapesWellFormed,
  expectCandlesFillPlot,
  expectCandlesRendered,
  expectChartTypeSelected,
  expectLineRendered,
  expectNoCandles,
  expectNoCandleHoverLine,
  expectOhlcTooltip,
  hoverMiddleCandle,
  movePointerOffChart,
  selectChartType,
} from './priceChart.specHelpers'

test.describe('price chart types UI integration', () => {
  test('opens on the line chart', async ({ page }) => {
    await goToRoute(page, 'dashboard')

    await expectChartTypeSelected(page, 'Line')
    await expectLineRendered(page)
    await expectNoCandles(page)
  })

  test('draws OHLC candles when switched to candles', async ({ page }) => {
    await goToRoute(page, 'dashboard')

    await selectChartType(page, 'Candles')

    await expectChartTypeSelected(page, 'Candles')
    await expectCandlesRendered(page)
    await expectCandleShapesWellFormed(page)
  })

  test('scales candles to fill the plot rather than a sliver', async ({
    page,
  }) => {
    await goToRoute(page, 'dashboard')

    await selectChartType(page, 'Candles')
    await expectCandlesRendered(page)

    await expectCandlesFillPlot(page)
  })

  test('switches back to the line chart', async ({ page }) => {
    await goToRoute(page, 'dashboard')

    await selectChartType(page, 'Candles')
    await expectCandlesRendered(page)

    await selectChartType(page, 'Line')

    await expectLineRendered(page)
    await expectNoCandles(page)
  })

  test('renders candles on mobile without horizontal scrolling', async ({
    page,
  }) => {
    await page.setViewportSize(MOBILE_VIEWPORT)
    await goToRoute(page, 'dashboard')

    await selectChartType(page, 'Candles')

    await expectCandlesRendered(page)
    await expectCandleShapesWellFormed(page)
    await expectNoHorizontalScroll(page)
  })
})

test.describe('candle hover marker UI integration', () => {
  test('marks the hovered candle with a vertical line', async ({ page }) => {
    await goToRoute(page, 'dashboard')
    await selectChartType(page, 'Candles')
    await expectCandlesRendered(page)

    await hoverMiddleCandle(page)

    await expectCandleHoverLine(page)
  })

  test('clears the marker when the pointer leaves the chart', async ({
    page,
  }) => {
    await goToRoute(page, 'dashboard')
    await selectChartType(page, 'Candles')
    await expectCandlesRendered(page)
    await hoverMiddleCandle(page)
    await expectCandleHoverLine(page)

    await movePointerOffChart(page)

    await expectNoCandleHoverLine(page)
  })

  test('shows the OHLC tooltip alongside the marker', async ({ page }) => {
    await goToRoute(page, 'dashboard')
    await selectChartType(page, 'Candles')
    await expectCandlesRendered(page)

    await hoverMiddleCandle(page)

    await expectCandleHoverLine(page)
    await expectOhlcTooltip(page)
  })
})
