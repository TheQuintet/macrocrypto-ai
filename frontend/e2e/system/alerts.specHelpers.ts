import { expect, type Page } from '@playwright/test'

export async function expectAlertsLoadedFromGateway(page: Page) {
  await expect(page.getByText('Failed to load alerts')).toHaveCount(0)
}

export async function expectAlertKindTabsVisible(page: Page) {
  await expect(page.getByRole('button', { name: /Price Alerts \(\d+\)/ })).toBeVisible()
  await expect(page.getByRole('button', { name: /Macro Alerts \(\d+\)/ })).toBeVisible()
  await expect(
    page.getByRole('button', { name: /Prediction Alerts \(\d+\)/ }),
  ).toBeVisible()
}
