import { test } from '@playwright/test'
import {
  expectCandleIntervalSelected,
  selectCandleInterval,
} from './priceChart.specHelpers'
import {
  clickSidebarNav,
  expectPageHeading,
  expectRoute,
  expectTimeRangeSelected,
  goToRoute,
  selectTimeRange,
} from './routing.specHelpers'

test.describe('client routing UI integration', () => {
  test('sidebar navigation updates the URL', async ({ page }) => {
    await goToRoute(page, 'dashboard')

    await clickSidebarNav(page, 'macro')
    await expectRoute(page, 'macro')
    await expectPageHeading(page, 'macro')

    await clickSidebarNav(page, 'forecasts')
    await expectRoute(page, 'forecasts')
    await expectPageHeading(page, 'forecasts')
  })

  test('deep links open the matching page', async ({ page }) => {
    await goToRoute(page, 'alerts')

    await expectRoute(page, 'alerts')
    await expectPageHeading(page, 'alerts')
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
