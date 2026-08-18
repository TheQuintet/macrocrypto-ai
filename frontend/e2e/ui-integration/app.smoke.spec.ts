import { test } from '@playwright/test'
import { expectPageHeading, goToRoute } from './routing.specHelpers'
import { expectPriceRendered } from './priceDisplay.specHelpers'

test.describe('app smoke', () => {
  test('loads the dashboard', async ({ page }) => {
    await goToRoute(page, 'dashboard')

    await expectPageHeading(page, 'dashboard')
    await expectPriceRendered(page)
  })
})
