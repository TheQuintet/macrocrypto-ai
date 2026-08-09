import { expect, test } from '@playwright/test'
import { expectPageHeading, goToRoute } from './routing.specHelpers'

test.describe('app smoke', () => {
  test('loads the dashboard', async ({ page }) => {
    await goToRoute(page, 'dashboard')

    await expectPageHeading(page, 'dashboard')
    await expect(
      page.getByRole('button', { name: /get started/i }),
    ).toBeVisible()
  })
})
