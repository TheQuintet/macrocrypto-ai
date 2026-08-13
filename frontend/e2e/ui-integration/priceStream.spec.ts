import { test } from '@playwright/test'
import { goToRoute } from './routing.specHelpers'
import {
  MOBILE_VIEWPORT,
  expectFeedKeepsUpdating,
  expectFeedLive,
  expectFeedRecoversFromDrop,
  expectLastUpdatedShown,
  expectPriceRendered,
} from './priceDisplay.specHelpers'

test.describe('price stream UI integration', () => {
  test('connects to the price stream and reports it as live', async ({
    page,
  }) => {
    await goToRoute(page, 'dashboard')

    await expectPriceRendered(page)
    await expectFeedLive(page)
  })

  test('shows the timestamp of the last update', async ({ page }) => {
    await goToRoute(page, 'dashboard')

    await expectFeedLive(page)
    await expectLastUpdatedShown(page)
  })

  test('renders incoming updates as they arrive', async ({ page }) => {
    await goToRoute(page, 'dashboard')

    await expectFeedLive(page)
    await expectFeedKeepsUpdating(page)
  })

  test('shows the connection status on mobile too', async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT)
    await goToRoute(page, 'dashboard')

    await expectFeedLive(page)
    await expectLastUpdatedShown(page)
  })

  test('reconnects on its own after the connection drops', async ({ page }) => {
    test.slow()
    await goToRoute(page, 'dashboard')

    await expectFeedLive(page)
    await expectFeedRecoversFromDrop(page)
  })
})
