import { expect, test } from '@playwright/test'
import {
  expectTimeRangeSelected,
  goToRoute,
  selectTimeRange,
} from './routing.specHelpers'
import {
  DESKTOP_VIEWPORT,
  MOBILE_VIEWPORT,
  TABLET_VIEWPORT,
  expectNoHorizontalScroll,
} from './priceDisplay.specHelpers'
import {
  expectCandlesRendered,
  hoverMiddleCandle,
} from './priceChart.specHelpers'
import {
  expectAsOfIndicatorTooltip,
  expectCardsAbovePriceChart,
  expectHistoryChartResizes,
  expectIndicatorCards,
  expectIndicatorCardsStacked,
  expectMacroPageLayout,
  expectTimeRangeOverPriceChart,
  expectTouchFriendlyIndicatorControls,
  expectHistoryUnderPriceChart,
  expectOnlyChartTimeRanges,
  expectIndicatorFilterSelected,
  expectTableShowsOnlyIndicator,
  selectIndicatorFilter,
} from './macroIndicators.specHelpers'

test.describe('macro indicators UI integration', () => {
  test('shows cards above a shared-window candle and history chart', async ({
    page,
  }) => {
    await goToRoute(page, 'macro')

    await expectMacroPageLayout(page)
    await expectCardsAbovePriceChart(page)
    await expectTimeRangeOverPriceChart(page)
    await expectHistoryUnderPriceChart(page)
    await expectOnlyChartTimeRanges(page)
    await expectTimeRangeSelected(page, '30d')
  })

  test('opens the BTC chart on candlesticks', async ({ page }) => {
    await goToRoute(page, 'macro')

    await expectCandlesRendered(page)
  })

  test('shows as-of indicator prints on the hovered candle', async ({
    page,
  }) => {
    await goToRoute(page, 'macro')
    await expectCandlesRendered(page)

    await hoverMiddleCandle(page)

    await expectAsOfIndicatorTooltip(page)
  })

  test('uses one time range for candles and indicator history', async ({
    page,
  }) => {
    await goToRoute(page, 'macro')

    await expectIndicatorCards(page)
    await selectTimeRange(page, '90d')
    await expectTimeRangeSelected(page, '90d')
    await expectIndicatorCards(page)
    await expectCandlesRendered(page)
    await expect(
      page.getByRole('img', { name: /macro indicator history/i }),
    ).toBeVisible()
  })

  test('stacks cards on mobile without horizontal scrolling', async ({
    page,
  }) => {
    await page.setViewportSize(MOBILE_VIEWPORT)
    await goToRoute(page, 'macro')

    await expectIndicatorCards(page)
    await expectIndicatorCardsStacked(page)
    await expectTouchFriendlyIndicatorControls(page)
    await expectNoHorizontalScroll(page)
  })

  test('keeps the history chart inside the mobile viewport', async ({
    page,
  }) => {
    await page.setViewportSize(MOBILE_VIEWPORT)
    await goToRoute(page, 'macro')

    await expectHistoryChartResizes(page)
    await expectNoHorizontalScroll(page)
  })

  test('renders on tablet without horizontal scrolling', async ({ page }) => {
    await page.setViewportSize(TABLET_VIEWPORT)
    await goToRoute(page, 'macro')

    await expectIndicatorCards(page)
    await expectNoHorizontalScroll(page)
  })

  test('uses a series dropdown on mobile instead of crowded pills', async ({
    page,
  }) => {
    await page.setViewportSize(MOBILE_VIEWPORT)
    await goToRoute(page, 'macro')

    await expect(
      page.getByRole('combobox', { name: 'Indicator filter' }),
    ).toBeVisible()
    await expect(
      page.getByRole('group', { name: 'Indicator filter' }),
    ).toHaveCount(0)

    await selectIndicatorFilter(page, 'Fed funds')
    await expectIndicatorFilterSelected(page, 'Fed funds')
    await expectTableShowsOnlyIndicator(page, 'federal_funds_rate')
    await expectNoHorizontalScroll(page)
  })

  test('filters indicator history to a single series', async ({ page }) => {
    await goToRoute(page, 'macro')

    await selectIndicatorFilter(page, 'CPI')
    await expectIndicatorFilterSelected(page, 'CPI')
    await expectTableShowsOnlyIndicator(page, 'cpi')
    await expect(
      page.getByRole('img', { name: /macro indicator history/i }),
    ).toBeVisible()
  })

  test('renders on desktop without horizontal scrolling', async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT)
    await goToRoute(page, 'macro')

    await expectIndicatorCards(page)
    await expectNoHorizontalScroll(page)
  })
})
