import { expect, test } from '@playwright/test'

test.describe('time range UI integration', () => {
  test('selection on dashboard is shown on macro indicators', async ({
    page,
  }) => {
    await page.goto('/')

    await expect(
      page.getByRole('heading', { name: /dashboard/i }),
    ).toBeVisible()

    await page.getByRole('button', { name: '30d', exact: true }).click()
    await expect(
      page.getByRole('button', { name: '30d', exact: true }),
    ).toHaveAttribute('aria-pressed', 'true')

    await page.getByRole('button', { name: 'Macro indicators' }).click()

    await expect(
      page.getByRole('heading', { name: /macro indicators/i }),
    ).toBeVisible()
    await expect(page.getByText(/showing data for/i)).toContainText('30d')
  })
})
