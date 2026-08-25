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
    page.getByRole('region', { name: /historical indicator observations/i }),
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

export async function expectIndicatorCardsStacked(page: Page) {
  const cards = page.locator('[data-slot="card"]')
  await expect(cards.first()).toBeVisible({ timeout: 10_000 })
  const count = await cards.count()
  expect(count).toBeGreaterThan(1)

  const first = await cards.nth(0).boundingBox()
  const second = await cards.nth(1).boundingBox()
  expect(first).not.toBeNull()
  expect(second).not.toBeNull()
  expect(second!.y).toBeGreaterThan(first!.y)
}

export async function expectTouchFriendlyIndicatorControls(page: Page) {
  const button = page
    .getByRole('group', { name: 'Indicator view' })
    .getByRole('button')
    .first()

  const box = await button.boundingBox()
  expect(box?.height ?? 0).toBeGreaterThanOrEqual(40)
}

export async function expectHistoryChartResizes(page: Page) {
  const chart = page.getByRole('img', { name: /cpi history/i })
  await expect(chart).toBeVisible({ timeout: 10_000 })
  const box = await chart.boundingBox()
  const viewportWidth = page.viewportSize()?.width ?? 0
  expect(box).not.toBeNull()
  expect(box!.width).toBeGreaterThan(0)
  expect((box!.x ?? 0) + (box!.width ?? 0)).toBeLessThanOrEqual(viewportWidth + 1)
}
