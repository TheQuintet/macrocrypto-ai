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
  expectAccuracyComparison,
  expectAccuracyComparisonTooltip,
  expectAccuracyDetailsCharts,
  expectAccuracyDetailsFacts,
  expectAccuracyTrend,
  expectAccuracyTrendTooltip,
  expectAccuracyWarning,
  expectNoAccuracyWarning,
  hoverAccuracyComparison,
  hoverAccuracyTrend,
  openAccuracyDetails,
  showAccuracyComparison,
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
  expectCoverageLevels,
  expectDateTicks,
  expectForecastLineOnly,
  expectForecastMadeAt,
  expectForecastStartDivider,
  expectLegendNames,
  expectLegendOmits,
  expectConfidenceSelected,
  expectHorizonSelected,
  expectKeyLevels,
  expectLegendExplains,
  expectPredictedLineRendered,
  expectPredictionTooltip,
  expectRangeCoverage,
  expectRangeWidthIndicator,
  expectSummaryStat,
  expectTooltipConfidence,
  keyLevelSpread,
  hoverForecast,
  hoverHistory,
  expectCandleTooltip,
  selectConfidence,
  selectHorizon,
  tapForecast,
  accuracyComparisonSpanDays,
  accuracyTrendPaths,
  expectAccuracyDetailsFocused,
  expectAccuracyStacked,
  expectBreakdownGraded,
  expectFocusBackOnViewDetails,
  expectFocusInsideDetails,
  expectMarketTileGraded,
  expectMarketTiles,
  expectMarketTilesTwoByTwo,
  pressEscape,
  pressTabInDetails,
  selectComparisonHorizon,
  tapAccuracyTrend,
  zoomAccuracyComparison,
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
    await expectForecastStartDivider(page, '24h')
  })

  test('draws the forecast forward only, with no model-fit line', async ({
    page,
  }) => {
    await goToRoute(page, 'forecasts')
    await expectChartRendered(page, '24h')
    await expectCandlesRendered(page, '24h')

    await expectForecastLineOnly(page, '24h')
    await expectLegendOmits(page, 'Model fit')
  })

  test('says when the forecast was made', async ({ page }) => {
    await goToRoute(page, 'forecasts')
    await expectChartRendered(page, '24h')

    await expectForecastMadeAt(page)
  })

  test('explains what the shaded band means', async ({ page }) => {
    await goToRoute(page, 'forecasts')
    await expectChartRendered(page, '24h')

    await expectLegendExplains(page, '85%')
    await expectLegendNames(page, [
      'Actual price',
      'Forecast',
      '85% confidence band',
    ])
  })

  test('summarises the window next to the chart', async ({ page }) => {
    await goToRoute(page, 'forecasts')
    await expectChartRendered(page, '24h')

    await expectSummaryStat(page, 'Current price', /\$[\d,]+\.\d{2}/)
    await expectSummaryStat(page, 'Expected change', /[+-]\d+\.\d{2}%/)
    await expectRangeCoverage(page, '85%')
    await expectCoverageLevels(page)
    await expectKeyLevels(page, /Widest hourly bounds across the 24-hour forecast/)
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
    await expectForecastStartDivider(page, '24h')
  })

  test('zooms the 7d history out past its resting week', async ({ page }) => {
    await goToRoute(page, 'forecasts')
    await selectHorizon(page, '7d')
    await expectChartRendered(page, '7d')
    await expectCandleCount(page, '7d', 168)

    await zoomHistoryOut(page)

    await expectCandleCountAbove(page, '7d', 168)
    await expectConfidenceBandRendered(page, '7d')
  })

  test('resets the window when the horizon changes', async ({ page }) => {
    await goToRoute(page, 'forecasts')
    await expectCandlesRendered(page, '24h')
    await zoomHistoryOut(page)
    await zoomHistoryOut(page)

    await selectHorizon(page, '7d')
    await expectChartRendered(page, '7d')

    // A week of hourly candles behind a week of hourly forecast.
    await expectCandleCount(page, '7d', 168)
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
    await expectKeyLevels(page, /Widest hourly bounds across the 7-day forecast/)
    await expectDateTicks(page, '7d')
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
    await expectRangeCoverage(page, '70%')
    const narrowSpread = await keyLevelSpread(page)
    const narrowPath = await bandPath(page, '24h')

    await selectConfidence(page, '95%')
    await expectConfidenceSelected(page, '95%')
    await expectRangeCoverage(page, '95%')

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
    await expectRangeCoverage(page, '70%')
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

  test('trends 24h and 7d together, with each value on hover', async ({
    page,
  }) => {
    await goToRoute(page, 'forecasts')
    await expectAccuracyTrend(page)

    await hoverAccuracyTrend(page)

    await expectAccuracyTrendTooltip(page)
  })

  test('keeps the trend on both horizons when the toggle moves', async ({
    page,
  }) => {
    await goToRoute(page, 'forecasts')
    await expectAccuracyTrend(page)
    const before = await accuracyTrendPaths(page)

    await selectHorizon(page, '7d')
    await expectAccuracyGrades(page, '7d')

    await expectAccuracyTrend(page)
    expect(await accuracyTrendPaths(page)).toEqual(before)
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

  test('compares predicted with actual price and follows the page toggle', async ({
    page,
  }) => {
    await goToRoute(page, 'forecasts')
    await expectAccuracyScore(page)

    await showAccuracyComparison(page)
    await expectAccuracyComparison(page, '24h')

    await selectHorizon(page, '7d')
    await expectAccuracyComparison(page, '7d')

    await hoverAccuracyComparison(page, '7d')
    await expectAccuracyComparisonTooltip(page)
  })

  test("switches the comparison from its own toggle, and the page's follows", async ({
    page,
  }) => {
    await goToRoute(page, 'forecasts')
    await expectAccuracyScore(page)
    await showAccuracyComparison(page)
    await expectAccuracyComparison(page, '24h')

    await selectComparisonHorizon(page, '7d')

    await expectAccuracyComparison(page, '7d')
    await expectHorizonSelected(page, '7d')
    await expectAccuracyGrades(page, '7d')
    await expectChartRendered(page, '7d')
  })

  test('zooms the comparison in on recent forecasts and back out', async ({
    page,
  }) => {
    await goToRoute(page, 'forecasts')
    await showAccuracyComparison(page)
    await expectAccuracyComparison(page, '24h')
    const full = await accuracyComparisonSpanDays(page)

    await zoomAccuracyComparison(page, 'in')
    await expect
      .poll(() => accuracyComparisonSpanDays(page))
      .toBeLessThan(full)

    await zoomAccuracyComparison(page, 'out')
    await expect.poll(() => accuracyComparisonSpanDays(page)).toBe(full)
    await expectAccuracyComparison(page, '24h')
  })

  test('grades each market on the card: yellow on 24h, red on 7d', async ({
    page,
  }) => {
    await goToRoute(page, 'forecasts')
    await expectAccuracyScore(page)

    await expectMarketTiles(page)
    await expectMarketTileGraded(page, 'Bull market', 'good')
    await expectMarketTileGraded(page, 'Bear market', 'medium')

    await selectHorizon(page, '7d')
    await expectAccuracyGrades(page, '7d')

    await expectMarketTileGraded(page, 'Bull market', 'good')
    await expectMarketTileGraded(page, 'Bear market', 'poor')
    await expectMarketTileGraded(page, 'Volatile', 'poor')
  })

  test('opens the full scorecard and closes it, returning focus', async ({
    page,
  }) => {
    await goToRoute(page, 'forecasts')
    await expectAccuracyScore(page)

    const dialog = await openAccuracyDetails(page)
    await expectAccuracyDetailsFocused(page)
    await expectAccuracyDetailsFacts(dialog)
    await expectAccuracyDetailsCharts(dialog, '24h')
    await expectAccuracyBreakdown(page)

    await closeAccuracyDetails(page)
    await expectAccuracyDetailsClosed(page)
    await expectFocusBackOnViewDetails(page)
  })

  test('keeps keyboard focus inside the scorecard and closes on Escape', async ({
    page,
  }) => {
    await goToRoute(page, 'forecasts')
    await expectAccuracyScore(page)
    await openAccuracyDetails(page)

    for (let step = 0; step < 12; step += 1) {
      await pressTabInDetails(page)
      await expectFocusInsideDetails(page)
    }

    await pressEscape(page)
    await expectAccuracyDetailsClosed(page)
    await expectFocusBackOnViewDetails(page)
  })

  test('grades the scorecard market table like the tiles', async ({ page }) => {
    await goToRoute(page, 'forecasts')
    await expectAccuracyScore(page)
    await selectHorizon(page, '7d')
    await expectAccuracyGrades(page, '7d')

    const dialog = await openAccuracyDetails(page)

    await expectBreakdownGraded(dialog, 'Bull market', 'good')
    await expectBreakdownGraded(dialog, 'Neutral', 'good')
    await expectBreakdownGraded(dialog, 'Bear market', 'poor')
    await expectBreakdownGraded(dialog, 'Volatile', 'poor')
  })
})

test.describe('forecast accuracy responsive UI integration', () => {
  for (const [name, viewport] of [
    ['desktop', DESKTOP_VIEWPORT],
    ['tablet', TABLET_VIEWPORT],
    ['mobile', MOBILE_VIEWPORT],
  ] as const) {
    test(`fits the accuracy card on ${name} without horizontal scrolling`, async ({
      page,
    }) => {
      await page.setViewportSize(viewport)
      await goToRoute(page, 'forecasts')

      await expectAccuracyScore(page)
      await expectAccuracyTrend(page)
      await expectMarketTiles(page)
      await expectNoHorizontalScroll(page)

      await showAccuracyComparison(page)
      await expectAccuracyComparison(page, '24h')
      await expectNoHorizontalScroll(page)

      await openAccuracyDetails(page)
      await expectNoHorizontalScroll(page)
    })
  }

  test('stacks the accuracy card on mobile, markets two by two', async ({
    page,
  }) => {
    await page.setViewportSize(MOBILE_VIEWPORT)
    await goToRoute(page, 'forecasts')
    await expectAccuracyTrend(page)

    await expectAccuracyStacked(page)
    await expectMarketTilesTwoByTwo(page)
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

  test('reaches the accuracy trend tooltip by touch', async ({ page }) => {
    await goToRoute(page, 'forecasts')
    await expectAccuracyTrend(page)

    await tapAccuracyTrend(page)

    await expectAccuracyTrendTooltip(page)
  })
})
