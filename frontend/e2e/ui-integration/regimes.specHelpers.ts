import { expect, type Page } from '@playwright/test'

export function regimeCard(page: Page) {
  return page
    .locator('[data-slot="card"]')
    .filter({ hasText: 'Macro regime' })
}

export function timelineSection(page: Page) {
  return page.getByRole('region', { name: 'Historical macro regimes' })
}

export function performanceSection(page: Page) {
  return page.getByRole('region', {
    name: 'BTC performance by macro regime',
  })
}

export async function expectRegimeCardClassified(page: Page) {
  const card = regimeCard(page)
  await expect(card).toBeVisible({ timeout: 10_000 })
  await expect(card.getByText('Not classified')).toHaveCount(0)
  await expect(
    card.getByRole('meter', { name: /regime classification confidence/i }),
  ).toBeVisible()
}

/** The card must name a regime, not leave the title as a skeleton. */
export async function expectRegimeCardNamesARegime(page: Page) {
  const title = regimeCard(page).locator('[data-slot="card-title"]')
  await expect(title).toBeVisible({ timeout: 10_000 })
  await expect(title).not.toBeEmpty()
}

export async function expectTimelineSegments(page: Page, atLeast: number) {
  const segments = timelineSection(page).locator('[data-regime]')
  await expect(segments.first()).toBeVisible({ timeout: 10_000 })
  expect(await segments.count()).toBeGreaterThanOrEqual(atLeast)
}

export async function expectCurrentRegimeHighlighted(page: Page) {
  const current = timelineSection(page).locator('[data-current="true"]')
  await expect(current).toHaveCount(1)
  await expect(current).toBeVisible()
}

export async function hoverFirstSegment(page: Page) {
  await timelineSection(page).locator('[data-regime]').first().hover()
}

export async function expectSegmentTooltip(page: Page) {
  await expect(page.getByRole('tooltip').first()).toBeVisible({
    timeout: 10_000,
  })
}

export async function clickFirstSegment(page: Page) {
  await timelineSection(page).locator('[data-regime]').first().click()
}

export async function expectRegimeDetailsDialog(page: Page) {
  const dialog = page.getByRole('dialog')
  await expect(dialog).toBeVisible({ timeout: 10_000 })
  await expect(dialog).toContainText(/–/)
}

export async function closeDialog(page: Page) {
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog')).toHaveCount(0)
}

export function zoomInButton(page: Page) {
  return page.getByRole('button', {
    name: /zoom into the regime timeline/i,
  })
}

export function zoomOutButton(page: Page) {
  return page.getByRole('button', {
    name: /zoom out of the regime timeline/i,
  })
}

export async function expectZoomLevel(page: Page, label: string) {
  await expect(timelineSection(page).getByText(label, { exact: true })).toBeVisible()
}

/**
 * Zooming widens the band past its container, which is what makes the short
 * regimes separable — the section itself must not grow with it.
 */
export async function expectBandWidensWithoutBreakingLayout(page: Page) {
  const section = timelineSection(page)
  const before = await section.boundingBox()

  await zoomInButton(page).click()
  await expectZoomLevel(page, '2x')

  const after = await section.boundingBox()
  expect(before).not.toBeNull()
  expect(after).not.toBeNull()
  expect(Math.abs(after!.width - before!.width)).toBeLessThan(2)
}

export async function expectPerformanceMetrics(page: Page) {
  const section = performanceSection(page)
  await expect(section).toBeVisible({ timeout: 10_000 })

  for (const header of ['Regime', 'Avg return', 'Sharpe']) {
    await expect(
      section.getByRole('columnheader', { name: header }),
    ).toBeVisible()
  }
}

export async function expectPerformanceRows(page: Page, atLeast: number) {
  const rows = performanceSection(page).locator('[data-regime]')
  await expect(rows.first()).toBeVisible({ timeout: 10_000 })
  expect(await rows.count()).toBeGreaterThanOrEqual(atLeast)
}

export async function expectCurrentRegimeBadged(page: Page) {
  await expect(
    performanceSection(page).getByText('Current').first(),
  ).toBeVisible({ timeout: 10_000 })
}

/** Below `sm` the detail columns drop so the table still fits the screen. */
export async function expectNarrowTableDropsDetailColumns(page: Page) {
  const section = performanceSection(page)
  await expect(section).toBeVisible({ timeout: 10_000 })
  await expect(
    section.getByRole('columnheader', { name: 'Avg return' }),
  ).toBeVisible()
  await expect(
    section.getByRole('columnheader', { name: 'Max drawdown' }),
  ).toBeHidden()
}

export async function expectWideTableShowsDetailColumns(page: Page) {
  const section = performanceSection(page)
  await expect(section).toBeVisible({ timeout: 10_000 })
  await expect(
    section.getByRole('columnheader', { name: 'Max drawdown' }),
  ).toBeVisible()
  await expect(
    section.getByRole('columnheader', { name: 'Volatility' }),
  ).toBeVisible()
}

export async function expectSimulatedBadges(page: Page) {
  // No backend in a UI-integration run, so every regime view must own up to
  // running on stand-in data rather than looking like the real market.
  await expect(timelineSection(page).getByText('Simulated')).toBeVisible({
    timeout: 10_000,
  })
  await expect(performanceSection(page).getByText('Simulated')).toBeVisible()
}
