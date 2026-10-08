import { test } from '@playwright/test'
import { expectPriceRendered } from '../ui-integration/priceDisplay.specHelpers'
import {
  expectCurrentPage,
  goToRoute,
} from '../ui-integration/routing.specHelpers'
import { skipUnlessGatewayAvailable } from './gateway.specHelpers'

test.describe('system e2e — dashboard smoke', () => {
  test.beforeEach(async ({ request }) => {
    await skipUnlessGatewayAvailable(request)
  })

  test('loads dashboard with live BTC price from the gateway', async ({ page }) => {
    await goToRoute(page, 'dashboard')
    await expectCurrentPage(page, 'dashboard')
    await expectPriceRendered(page)
  })
})
