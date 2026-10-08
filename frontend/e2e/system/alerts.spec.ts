import { test } from '@playwright/test'
import {
  expectCurrentPage,
  goToRoute,
} from '../ui-integration/routing.specHelpers'
import {
  expectAlertKindTabsVisible,
  expectAlertsLoadedFromGateway,
} from './alerts.specHelpers'
import { skipUnlessGatewayAvailable } from './gateway.specHelpers'

test.describe('system e2e — alerts', () => {
  test.beforeEach(async ({ request }) => {
    await skipUnlessGatewayAvailable(request)
  })

  test('alerts page loads price, macro, and prediction tabs via gateway', async ({
    page,
  }) => {
    await goToRoute(page, 'alerts')
    await expectCurrentPage(page, 'alerts')
    await expectAlertsLoadedFromGateway(page)
    await expectAlertKindTabsVisible(page)
  })
})
