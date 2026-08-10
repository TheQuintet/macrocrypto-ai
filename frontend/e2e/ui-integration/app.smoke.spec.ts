import { expect, test } from '@playwright/test'

test.describe('app smoke', () => {
  test('loads the dashboard', async ({ page }) => {
    await page.goto('/')

    await expect(
      page.getByRole('heading', { name: /dashboard/i }),
    ).toBeVisible()
    await expect(
      page.getByRole('button', { name: /get started/i }),
    ).toBeVisible()
  })
})
