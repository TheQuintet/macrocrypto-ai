import { test } from '@playwright/test'
import {
  clickSidebarNav,
  expectCurrentPage,
  expectRoute,
  goToRoute,
} from '../ui-integration/routing.specHelpers'
import { skipUnlessGatewayAvailable } from './gateway.specHelpers'

test.describe('system e2e — navigation with live APIs', () => {
  test.beforeEach(async ({ request }) => {
    await skipUnlessGatewayAvailable(request)
  })

  test('sidebar routes load macro, forecasts, and calendar', async ({ page }) => {
    await goToRoute(page, 'dashboard')

    await clickSidebarNav(page, 'macro')
    await expectRoute(page, 'macro')
    await expectCurrentPage(page, 'macro')

    await clickSidebarNav(page, 'forecasts')
    await expectRoute(page, 'forecasts')
    await expectCurrentPage(page, 'forecasts')

    await clickSidebarNav(page, 'calendar')
    await expectRoute(page, 'calendar')
    await expectCurrentPage(page, 'calendar')
  })
})
