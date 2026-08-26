import { expect, type Page } from '@playwright/test'

export async function expectMacroPageLayout(page: Page) {
  await expectIndicatorCards(page)
  await expect(
    page.getByRole('group', { name: 'Time range' }),
  ).toBeVisible()
  await expect(
    page.getByRole('group', { name: 'Historical period' }),
  ).toHaveCount(0)
  await expect(
    page.getByRole('heading', { name: 'BTC price' }),
  ).toBeVisible()
  await expect(
    page.getByRole('group', { name: 'Chart type' }),
  ).toHaveCount(0)
  await expect(
    page.getByRole('img', { name: /macro indicator history/i }),
  ).toBeVisible({ timeout: 10_000 })
}

export async function expectTimeRangeOverPriceChart(page: Page) {
  const heading = page.getByRole('heading', { name: 'BTC price' })
  const picker = page.getByRole('group', { name: 'Time range' })
  await expect(heading).toBeVisible()
  await expect(picker).toBeVisible()

  const headingBox = await heading.boundingBox()
  const pickerBox = await picker.boundingBox()
  expect(headingBox).not.toBeNull()
  expect(pickerBox).not.toBeNull()
  expect(pickerBox!.x).toBeLessThanOrEqual(headingBox!.x + 24)
  expect(pickerBox!.y).toBeLessThan(headingBox!.y + 80)
}

export async function expectCardsAbovePriceChart(page: Page) {
  const card = page.getByText(/^cpi$/i).first()
  const chart = page.getByRole('heading', { name: 'BTC price' })
  await expect(card).toBeVisible({ timeout: 10_000 })
  await expect(chart).toBeVisible()

  const cardBox = await card.boundingBox()
  const chartBox = await chart.boundingBox()
  expect(cardBox).not.toBeNull()
  expect(chartBox).not.toBeNull()
  expect(chartBox!.y).toBeGreaterThan(cardBox!.y)
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

export async function expectHistoryUnderPriceChart(page: Page) {
  const btc = page.getByRole('heading', { name: 'BTC price' })
  const chart = page.getByRole('img', { name: /macro indicator history/i })
  const history = page.getByRole('heading', { name: 'Indicator history' })
  await expect(btc).toBeVisible()
  await expect(chart).toBeVisible({ timeout: 10_000 })
  await expect(history).toBeVisible()

  const btcBox = await btc.boundingBox()
  const chartBox = await chart.boundingBox()
  const historyBox = await history.boundingBox()
  expect(btcBox).not.toBeNull()
  expect(chartBox).not.toBeNull()
  expect(historyBox).not.toBeNull()
  expect(chartBox!.y).toBeGreaterThan(btcBox!.y)
  expect(historyBox!.y).toBeGreaterThan(chartBox!.y)
  expect(Math.abs(historyBox!.x - btcBox!.x)).toBeLessThan(48)
}

export async function expectOnlyChartTimeRanges(page: Page) {
  const picker = page.getByRole('group', { name: 'Time range' })
  await expect(picker).toBeVisible()

  for (const range of ['30d', '90d', '1y', '5y'] as const) {
    await expect(
      picker.getByRole('button', { name: range, exact: true }),
    ).toBeVisible()
  }

  for (const range of ['24h', '7d', '6m'] as const) {
    await expect(
      picker.getByRole('button', { name: range, exact: true }),
    ).toHaveCount(0)
  }
}

export async function expectTouchFriendlyIndicatorControls(page: Page) {
  const button = page
    .getByRole('group', { name: 'Time range' })
    .getByRole('button')
    .first()

  const box = await button.boundingBox()
  expect(box?.height ?? 0).toBeGreaterThanOrEqual(40)
}

export async function selectIndicatorFilter(page: Page, label: string) {
  const combo = page.getByRole('combobox', { name: 'Indicator filter' })
  if (await combo.isVisible()) {
    await combo.selectOption({ label })
    return
  }

  const filter = page.getByRole('group', { name: 'Indicator filter' })
  await expect(filter).toBeVisible()
  await filter.getByRole('button', { name: label, exact: true }).click()
}

export async function expectIndicatorFilterSelected(page: Page, label: string) {
  const combo = page.getByRole('combobox', { name: 'Indicator filter' })
  if (await combo.isVisible()) {
    await expect(combo).toHaveValue(filterValueForLabel(label))
    return
  }

  await expect(
    page
      .getByRole('group', { name: 'Indicator filter' })
      .getByRole('button', { name: label, exact: true }),
  ).toHaveAttribute('aria-pressed', 'true')
}

function filterValueForLabel(label: string) {
  const option = {
    All: 'all',
    CPI: 'cpi',
    'Fed funds': 'federal_funds_rate',
    'FED FUNDS': 'federal_funds_rate',
    GDP: 'gdp',
  }[label]
  if (!option) {
    throw new Error(`Unknown indicator filter label: ${label}`)
  }
  return option
}

export async function expectTableShowsOnlyIndicator(page: Page, name: string) {
  const table = page.getByRole('region', {
    name: /historical indicator observations/i,
  })
  await expect(table).toBeVisible({ timeout: 10_000 })
  const names = table.locator('[data-indicator]')
  await expect(names.first()).toBeVisible()
  const count = await names.count()
  expect(count).toBeGreaterThan(0)
  for (let index = 0; index < count; index += 1) {
    await expect(names.nth(index)).toHaveAttribute('data-indicator', name)
  }
}

export async function expectAsOfIndicatorTooltip(page: Page) {
  const tooltip = page.getByRole('tooltip').filter({ hasText: 'Open' })
  await expect(tooltip).toBeVisible({ timeout: 10_000 })
  for (const label of ['High', 'Low', 'Close']) {
    await expect(tooltip).toContainText(label)
  }
  await expect(tooltip).toContainText(/cpi/i)
}

export async function expectHistoryChartResizes(page: Page) {
  const chart = page.getByRole('img', { name: /macro indicator history/i })
  await expect(chart).toBeVisible({ timeout: 10_000 })
  const box = await chart.boundingBox()
  const viewportWidth = page.viewportSize()?.width ?? 0
  expect(box).not.toBeNull()
  expect(box!.width).toBeGreaterThan(0)
  expect((box!.x ?? 0) + (box!.width ?? 0)).toBeLessThanOrEqual(
    viewportWidth + 1,
  )
}
