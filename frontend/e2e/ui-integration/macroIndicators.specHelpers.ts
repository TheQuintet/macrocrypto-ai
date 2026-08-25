import { expect, type Page } from '@playwright/test'

export async function selectIndicatorView(page: Page, label: 'Current' | 'Historical') {
  await page.getByRole('button', { name: label, exact: true }).click()
}

export async function selectHistoricalPeriod(page: Page, period: string) {
  await page
    .getByRole('group', { name: 'Historical period' })
    .getByRole('button', { name: period, exact: true })
    .click()
}

export async function expectCurrentIndicatorView(page: Page) {
  await expect(
    page.getByRole('button', { name: 'Current', exact: true }),
  ).toHaveAttribute('aria-pressed', 'true')
}

export async function expectHistoricalIndicatorView(page: Page) {
  await expect(
    page.getByRole('button', { name: 'Historical', exact: true }),
  ).toHaveAttribute('aria-pressed', 'true')
  await expect(
    page.getByRole('group', { name: 'Historical period' }),
  ).toBeVisible()
  await expect(
    page.getByRole('table', { name: /historical indicator observations/i }),
  ).toBeVisible({ timeout: 10_000 })
}

export async function expectPeriodSelected(page: Page, period: string) {
  await expect(
    page
      .getByRole('group', { name: 'Historical period' })
      .getByRole('button', { name: period, exact: true }),
  ).toHaveAttribute('aria-pressed', 'true')
}

export async function expectIndicatorCards(page: Page) {
  await expect(page.getByText(/^cpi$/i).first()).toBeVisible({
    timeout: 10_000,
  })
}
