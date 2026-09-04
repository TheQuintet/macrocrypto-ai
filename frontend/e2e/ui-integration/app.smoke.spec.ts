import { test } from '@playwright/test'
import { expectCurrentPage, goToRoute } from './routing.specHelpers'
import { expectPriceRendered } from './priceDisplay.specHelpers'

test.describe('app smoke', () => {
  test('loads the dashboard', async ({ page }) => {
    await goToRoute(page, 'dashboard')

    await expectCurrentPage(page, 'dashboard')
    await expectPriceRendered(page)
  })
})
