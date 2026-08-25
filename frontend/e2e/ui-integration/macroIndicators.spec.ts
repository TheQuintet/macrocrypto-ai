import { test } from '@playwright/test'
import { goToRoute } from './routing.specHelpers'
import {
  expectCurrentIndicatorView,
  expectHistoricalIndicatorView,
  expectIndicatorCards,
  expectPeriodSelected,
  selectIndicatorView,
  selectHistoricalPeriod,
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
})
