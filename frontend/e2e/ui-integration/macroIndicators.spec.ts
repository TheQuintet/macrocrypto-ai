import { test } from '@playwright/test'
import { goToRoute } from './routing.specHelpers'
import {
  DESKTOP_VIEWPORT,
  MOBILE_VIEWPORT,
  TABLET_VIEWPORT,
  expectNoHorizontalScroll,
} from './priceDisplay.specHelpers'
import {
  expectCurrentIndicatorView,
  expectHistoricalIndicatorView,
  expectHistoryChartResizes,
  expectIndicatorCards,
  expectIndicatorCardsStacked,
  expectPeriodSelected,
  expectTouchFriendlyIndicatorControls,
  selectHistoricalPeriod,
  selectIndicatorView,
} from './macroIndicators.specHelpers'

test.describe('macro indicators UI integration', () => {
  test('shows current indicators on the macro page', async ({ page }) => {
    await goToRoute(page, 'macro')

    await expectCurrentIndicatorView(page)
    await expectIndicatorCards(page)
  })

  test('toggles to historical charts and periods', async ({ page }) => {
    await goToRoute(page, 'macro')

    await selectIndicatorView(page, 'Historical')

    await expectHistoricalIndicatorView(page)
    await expectPeriodSelected(page, '90d')

    await selectHistoricalPeriod(page, '1y')
    await expectPeriodSelected(page, '1y')
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

  test('keeps historical charts inside the mobile viewport', async ({
    page,
  }) => {
    await page.setViewportSize(MOBILE_VIEWPORT)
    await goToRoute(page, 'macro')
    await selectIndicatorView(page, 'Historical')

    await expectHistoricalIndicatorView(page)
    await expectHistoryChartResizes(page)
    await expectNoHorizontalScroll(page)
  })

  test('renders on tablet without horizontal scrolling', async ({ page }) => {
    await page.setViewportSize(TABLET_VIEWPORT)
    await goToRoute(page, 'macro')

    await expectIndicatorCards(page)
    await expectNoHorizontalScroll(page)
  })

  test('renders on desktop without horizontal scrolling', async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT)
    await goToRoute(page, 'macro')

    await expectIndicatorCards(page)
    await expectNoHorizontalScroll(page)
  })
})
