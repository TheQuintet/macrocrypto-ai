import { test } from '@playwright/test'
import { goToRoute } from './routing.specHelpers'
import {
  DESKTOP_VIEWPORT,
  MOBILE_VIEWPORT,
  TABLET_VIEWPORT,
  expectChangeWindowsRendered,
  expectNoHorizontalScroll,
  expectPriceRendered,
  expectPriceWithinViewport,
  expectTouchFriendlyChartControls,
} from './priceDisplay.specHelpers'

test.describe('price display UI integration', () => {
  test('renders the current price and both change windows', async ({ page }) => {
    await goToRoute(page, 'dashboard')

    await expectPriceRendered(page)
    await expectChangeWindowsRendered(page)
  })

  test('renders on mobile without horizontal scrolling', async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT)
    await goToRoute(page, 'dashboard')

    await expectPriceRendered(page)
    await expectPriceWithinViewport(page)
    await expectNoHorizontalScroll(page)
  })

  test('keeps chart controls touch-friendly on mobile', async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT)
    await goToRoute(page, 'dashboard')

    await expectTouchFriendlyChartControls(page)
  })

  test('renders on tablet without horizontal scrolling', async ({ page }) => {
    await page.setViewportSize(TABLET_VIEWPORT)
    await goToRoute(page, 'dashboard')

    await expectPriceRendered(page)
    await expectNoHorizontalScroll(page)
  })

  test('renders on desktop without horizontal scrolling', async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT)
    await goToRoute(page, 'dashboard')

    await expectPriceRendered(page)
    await expectChangeWindowsRendered(page)
    await expectNoHorizontalScroll(page)
  })
})
