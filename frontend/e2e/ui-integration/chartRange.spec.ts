import { expect, test } from '@playwright/test'
import { goToRoute, selectTimeRange } from './routing.specHelpers'
import { expectCandleIntervalSelected } from './priceChart.specHelpers'
import {
  MOBILE_VIEWPORT,
  expectNoHorizontalScroll,
} from './priceDisplay.specHelpers'
import {
  probePlot,
  readVisibleSpanDays,
  waitForAnyCandles,
  waitForCandleCount,
  waitForCandlesToChangeFrom,
  zoomIn,
  zoomInButton,
  zoomOutButton,
} from './chartRange.specHelpers'

test.describe('chart fits the selected time range (#510)', () => {
  test('a wider range puts more of the market on screen', async ({ page }) => {
    await goToRoute(page, 'dashboard')

    await selectTimeRange(page, '30d')
    await waitForAnyCandles(page)
    const narrow = await probePlot(page)

    await selectTimeRange(page, '90d')
    const wide = await waitForCandlesToChangeFrom(page, narrow.candles)

    // The bug: the viewport windowed to roughly one screen of candles
    // regardless of range, so 90d looked identical to 30d.
    expect(wide).toBeGreaterThan(narrow.candles)
  })

  test('candles get denser as the range widens, rather than staying put', async ({
    page,
  }) => {
    await goToRoute(page, 'dashboard')

    await selectTimeRange(page, '30d')
    await waitForAnyCandles(page)
    const narrow = await probePlot(page)

    await selectTimeRange(page, '90d')
    await waitForCandlesToChangeFrom(page, narrow.candles)
    const wide = await probePlot(page)

    expect(narrow.medianCandleWidth).not.toBeNull()
    expect(wide.medianCandleWidth).not.toBeNull()
    expect(wide.medianCandleWidth!).toBeLessThan(narrow.medianCandleWidth!)
  })

  test('the reported window covers the range that was selected', async ({
    page,
  }) => {
    await goToRoute(page, 'dashboard')

    await selectTimeRange(page, '30d')
    await waitForAnyCandles(page)
    const narrowSpan = await readVisibleSpanDays(page)

    await selectTimeRange(page, '90d')
    await waitForCandlesToChangeFrom(page, 31)
    const wideSpan = await readVisibleSpanDays(page)

    expect(narrowSpan).toBeGreaterThanOrEqual(28)
    expect(narrowSpan).toBeLessThanOrEqual(32)
    expect(wideSpan).toBeGreaterThanOrEqual(85)
  })

  test('zoom still works after a range change', async ({ page }) => {
    await goToRoute(page, 'dashboard')

    await selectTimeRange(page, '90d')
    await waitForCandleCount(page, 91)
    const fitted = await probePlot(page)

    await zoomIn(page, 3)

    // Zooming in raises the density: the same buckets, drawn wider.
    await expect
      .poll(async () => (await probePlot(page)).medianCandleWidth ?? 0, {
        timeout: 20_000,
      })
      .toBeGreaterThan(fitted.medianCandleWidth!)
    await expect(zoomOutButton(page)).toBeEnabled()
  })

  test('1y and 5y still draw candlesticks', async ({ page }) => {
    await goToRoute(page, 'dashboard')

    await selectTimeRange(page, '1y')
    await expectCandleIntervalSelected(page, 'Weekly')
    await waitForAnyCandles(page)

    await selectTimeRange(page, '5y')
    await expectCandleIntervalSelected(page, 'Weekly')
    await waitForAnyCandles(page)
  })

  test('a year-long window is not reported as a single day', async ({
    page,
  }) => {
    await goToRoute(page, 'dashboard')

    await selectTimeRange(page, '1y')
    await waitForAnyCandles(page)

    // The candle axis labels carry no year, so reusing them here read as
    // "Sep 15 → Sep 15" for a whole year on screen.
    expect(await readVisibleSpanDays(page)).toBeGreaterThan(300)
  })

  test('fitting holds on a phone without sideways scroll', async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT)
    await goToRoute(page, 'dashboard')

    await selectTimeRange(page, '30d')
    await waitForAnyCandles(page)
    await expectNoHorizontalScroll(page)
    await expect(zoomInButton(page)).toBeEnabled()
  })
})
