import { test } from '@playwright/test'
import {
  expectCandleIntervalSelected,
  selectCandleInterval,
} from './priceChart.specHelpers'
import {
  clickManageAlerts,
  clickSidebarNav,
  expectNotificationsOpen,
  expectCurrentPage,
  expectRoute,
  expectTimeRangeSelected,
  goToRoute,
  openNotifications,
  selectTimeRange,
} from './routing.specHelpers'

test.describe('client routing UI integration', () => {
  test('sidebar navigation updates the URL', async ({ page }) => {
    await goToRoute(page, 'dashboard')

    await clickSidebarNav(page, 'macro')
    await expectRoute(page, 'macro')
    await expectCurrentPage(page, 'macro')

    await clickSidebarNav(page, 'forecasts')
    await expectRoute(page, 'forecasts')
    await expectCurrentPage(page, 'forecasts')

    await clickSidebarNav(page, 'alerts')
    await expectRoute(page, 'alerts')
    await expectCurrentPage(page, 'alerts')

    await clickSidebarNav(page, 'regimePerformance')
    await expectRoute(page, 'regimePerformance')
    await expectCurrentPage(page, 'regimePerformance')

    await clickSidebarNav(page, 'calendar')
    await expectRoute(page, 'calendar')
    await expectCurrentPage(page, 'calendar')

    await clickSidebarNav(page, 'economicNotifications')
    await expectRoute(page, 'economicNotifications')
    await expectCurrentPage(page, 'economicNotifications')
  })

  test('header bell opens notifications and can reach alert settings', async ({
    page,
  }) => {
    await goToRoute(page, 'dashboard')

    await openNotifications(page)
    await expectNotificationsOpen(page)
    await expectRoute(page, 'dashboard')

    await clickManageAlerts(page)
    await expectRoute(page, 'alerts')
    await expectCurrentPage(page, 'alerts')
  })

  test('deep links open the matching page', async ({ page }) => {
    await goToRoute(page, 'alerts')

    await expectRoute(page, 'alerts')
    await expectCurrentPage(page, 'alerts')
  })

  test('time range selection on dashboard is shown on macro indicators', async ({
    page,
  }) => {
    await goToRoute(page, 'dashboard')

    await selectTimeRange(page, '30d')
    await expectTimeRangeSelected(page, '30d')

    await clickSidebarNav(page, 'macro')
    await expectRoute(page, 'macro')
    await expectTimeRangeSelected(page, '30d')
  })

  test('candle interval selection on dashboard is shown on macro indicators', async ({
    page,
  }) => {
    await goToRoute(page, 'dashboard')

    await selectCandleInterval(page, 'Weekly')
    await expectCandleIntervalSelected(page, 'Weekly')

    await clickSidebarNav(page, 'macro')
    await expectRoute(page, 'macro')
    await expectCandleIntervalSelected(page, 'Weekly')
  })
})
