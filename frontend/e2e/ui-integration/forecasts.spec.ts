import { expect, test } from '@playwright/test'
import { goToRoute } from './routing.specHelpers'
import {
  DESKTOP_VIEWPORT,
  MOBILE_VIEWPORT,
  TABLET_VIEWPORT,
  expectNoHorizontalScroll,
} from './priceDisplay.specHelpers'
import {
  closeAccuracyDetails,
  expectAccuracyBreakdown,
  expectAccuracyDetailsClosed,
  expectAccuracyGrades,
  expectAccuracyScore,
  expectAccuracyTrend,
  expectAccuracyWarning,
  expectNoAccuracyWarning,
  openAccuracyDetails,
  bandPath,
  candleCount,
  expectCandleCount,
  expectCandleCountAbove,
  expectZoomInDisabled,
  zoomHistoryIn,
  zoomHistoryOut,
  expectCandlesRendered,
  expectChartRendered,
  expectConfidenceBandRendered,
  expectFitOverlaysHistory,
  expectLegendNames,
  expectNowDivider,
  expectConfidenceSelected,
  expectHorizonSelected,
  expectKeyLevels,
  expectLegendExplains,
  expectPredictedLineRendered,
  expectPredictionTooltip,
  expectRangeWidthIndicator,
  expectForecastConfidence,
  expectForecastConfidenceScale,
  expectSummaryStat,
  expectTooltipConfidence,
  keyLevelSpread,
  hoverForecast,
  hoverHistory,
  expectCandleTooltip,
  selectConfidence,
  selectHorizon,
  tapForecast,
} from './forecasts.specHelpers'

test.describe('forecast chart UI integration', () => {
  test('opens on the 24h forecast with its band and predicted path', async ({
    page,
  }) => {
    await goToRoute(page, 'forecasts')

    await expectChartRendered(page, '24h')
    await expectHorizonSelected(page, '24h')
    await expectPredictedLineRendered(page, '24h')
    await expectConfidenceBandRendered(page, '24h')
  })

  test('draws the actual price as candles behind the forecast', async ({
    page,
  }) => {
    await goToRoute(page, 'forecasts')
    await expectChartRendered(page, '24h')

    await expectCandlesRendered(page, '24h')
    await expectNowDivider(page, '24h')
  })

  test('runs the model through the history, not only past it', async ({
    page,
  }) => {
    await goToRoute(page, 'forecasts')
    await expectChartRendered(page, '24h')

    await expectFitOverlaysHistory(page, '24h')
  })

  test('explains what the shaded band means', async ({ page }) => {
    await goToRoute(page, 'forecasts')
    await expectChartRendered(page, '24h')

    await expectLegendExplains(page, '85%')
    await expectLegendNames(page, [
      'Actual price',
      'Model fit',
      'Forecast',
      '85% confidence band',
    ])
  })

  test('summarises the window next to the chart', async ({ page }) => {
    await goToRoute(page, 'forecasts')
    await expectChartRendered(page, '24h')

    await expectSummaryStat(page, 'Current price', /\$[\d,]+\.\d{2}/)
    await expectSummaryStat(page, 'Expected change', /[+-]\d+\.\d{2}%/)
    await expectForecastConfidence(page, '85%', 'moderate')
    await expectForecastConfidenceScale(page)
    await expectKeyLevels(page, /Widest hourly bounds/)
    await expectRangeWidthIndicator(page)
  })
})

test.describe('forecast history zoom UI integration', () => {
  test('opens with as much history as forecast, matching the label', async ({
    page,
  }) => {
    await goToRoute(page, 'forecasts')
    await expectChartRendered(page, '24h')
    await expectCandlesRendered(page, '24h')

    await expectCandleCount(page, '24h', 24)
    await expectZoomInDisabled(page)
  })

  test('reveals more history on zoom out and gives it back on zoom in', async ({
    page,
  }) => {
    await goToRoute(page, 'forecasts')
    await expectCandlesRendered(page, '24h')
    const atRest = await candleCount(page, '24h')

    await zoomHistoryOut(page)
    await expectCandleCountAbove(page, '24h', atRest)

    await zoomHistoryIn(page)
    await expectCandleCount(page, '24h', atRest)
  })

  test('keeps the forecast on screen however far the history is pulled back', async ({
    page,
  }) => {
    await goToRoute(page, 'forecasts')
    await expectCandlesRendered(page, '24h')

    for (let step = 0; step < 4; step += 1) {
      await zoomHistoryOut(page)
    }

    await expectConfidenceBandRendered(page, '24h')
    await expectNowDivider(page, '24h')
  })

  test('resets the window when the horizon changes', async ({ page }) => {
    await goToRoute(page, 'forecasts')
    await expectCandlesRendered(page, '24h')
    await zoomHistoryOut(page)
    await zoomHistoryOut(page)

    await selectHorizon(page, '7d')
    await expectChartRendered(page, '7d')

    await expectCandleCount(page, '7d', 7)
  })
})

test.describe('forecast horizon toggle UI integration', () => {
  test('switches the same chart and summary to the 7d window', async ({
    page,
  }) => {
    await goToRoute(page, 'forecasts')
    await expectChartRendered(page, '24h')

    await selectHorizon(page, '7d')

    await expectHorizonSelected(page, '7d')
    await expectChartRendered(page, '7d')
    await expectConfidenceBandRendered(page, '7d')
    await expectCandlesRendered(page, '7d')
    await expectKeyLevels(page, /Widest daily bounds/)
  })

  test('returns to the 24h window', async ({ page }) => {
    await goToRoute(page, 'forecasts')
    await selectHorizon(page, '7d')
    await expectChartRendered(page, '7d')

    await selectHorizon(page, '24h')

    await expectHorizonSelected(page, '24h')
    await expectChartRendered(page, '24h')
  })
})

test.describe('confidence level UI integration', () => {
  test('widens the band it shades as confidence rises', async ({ page }) => {
    await goToRoute(page, 'forecasts')
    await expectConfidenceBandRendered(page, '24h')

    await selectConfidence(page, '70%')
    await expectConfidenceSelected(page, '70%')
    await expectForecastConfidence(page, '70%', 'low')
    const narrowSpread = await keyLevelSpread(page)
    const narrowPath = await bandPath(page, '24h')

    await selectConfidence(page, '95%')
    await expectConfidenceSelected(page, '95%')
    await expectForecastConfidence(page, '95%', 'high')

    expect(await keyLevelSpread(page)).toBeGreaterThan(narrowSpread)
    expect(await bandPath(page, '24h')).not.toBe(narrowPath)
  })

  test('relabels the legend and summary with the chosen level', async ({
    page,
  }) => {
    await goToRoute(page, 'forecasts')
    await expectChartRendered(page, '24h')

    await selectConfidence(page, '70%')

    await expectLegendExplains(page, '70%')
    await expectForecastConfidence(page, '70%', 'low')
  })
})

test.describe('forecast tooltip UI integration', () => {
  test('shows the point detail on hover', async ({ page }) => {
    await goToRoute(page, 'forecasts')
    await expectChartRendered(page, '24h')

    await hoverForecast(page, '24h')

    await expectPredictionTooltip(page)
    await expectTooltipConfidence(page, '85%')
  })

  test('shows OHLC detail when hovering the actual price', async ({ page }) => {
    await goToRoute(page, 'forecasts')
    await expectChartRendered(page, '24h')

    await hoverHistory(page, '24h')

    await expectCandleTooltip(page)
  })

  test('carries the confidence level through to the 7d tooltip', async ({
    page,
  }) => {
    await goToRoute(page, 'forecasts')
    await selectHorizon(page, '7d')
    await selectConfidence(page, '95%')
    await expectChartRendered(page, '7d')

    await hoverForecast(page, '7d')

    await expectPredictionTooltip(page)
    await expectTooltipConfidence(page, '95%')
  })
})

test.describe('forecast responsive UI integration', () => {
  for (const [name, viewport] of [
    ['desktop', DESKTOP_VIEWPORT],
    ['tablet', TABLET_VIEWPORT],
    ['mobile', MOBILE_VIEWPORT],
  ] as const) {
    test(`renders the chart on ${name} without horizontal scrolling`, async ({
      page,
    }) => {
      await page.setViewportSize(viewport)
      await goToRoute(page, 'forecasts')

      await expectChartRendered(page, '24h')
      await expectConfidenceBandRendered(page, '24h')
      await expectNoHorizontalScroll(page)
    })
  }

  test('keeps the chart inside the viewport on mobile', async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT)
    await goToRoute(page, 'forecasts')
    await expectChartRendered(page, '24h')

    const box = await page
      .getByRole('img', { name: 'BTC 24h price forecast' })
      .boundingBox()

    expect(box).not.toBeNull()
    expect(box!.width).toBeLessThanOrEqual(MOBILE_VIEWPORT.width)
  })

  test('keeps the controls tappable on mobile', async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT)
    await goToRoute(page, 'forecasts')
    await expectChartRendered(page, '24h')

    await selectHorizon(page, '7d')

    await expectHorizonSelected(page, '7d')
    await expectChartRendered(page, '7d')
    await expectNoHorizontalScroll(page)
  })

})

test.describe('forecast accuracy UI integration', () => {
  test('grades past 24h forecasts under the chart', async ({ page }) => {
    await goToRoute(page, 'forecasts')

    await expectAccuracyScore(page)
    await expectAccuracyGrades(page, '24h')
    await expectAccuracyTrend(page)
    await expectNoAccuracyWarning(page)
  })

  test('follows the horizon toggle and shows the service warning', async ({
    page,
  }) => {
    await goToRoute(page, 'forecasts')
    await expectAccuracyScore(page)

    await selectHorizon(page, '7d')

    await expectAccuracyGrades(page, '7d')
    await expectAccuracyWarning(page)
  })

  test('opens and closes the full scorecard', async ({ page }) => {
    await goToRoute(page, 'forecasts')
    await expectAccuracyScore(page)

    await openAccuracyDetails(page)
    await expectAccuracyBreakdown(page)

    await closeAccuracyDetails(page)
    await expectAccuracyDetailsClosed(page)
  })

  test('fits the scorecard on mobile without horizontal scrolling', async ({
    page,
  }) => {
    await page.setViewportSize(MOBILE_VIEWPORT)
    await goToRoute(page, 'forecasts')

    await expectAccuracyScore(page)
    await expectNoHorizontalScroll(page)
  })
})

/** A real touch-capable context — `setViewportSize` alone leaves touch off. */
test.describe('forecast touch UI integration', () => {
  test.use({ viewport: MOBILE_VIEWPORT, hasTouch: true })

  test('reaches the tooltip by touch on mobile', async ({ page }) => {
    await goToRoute(page, 'forecasts')
    await expectChartRendered(page, '24h')

    await tapForecast(page, '24h')

    await expectPredictionTooltip(page)
  })
})
