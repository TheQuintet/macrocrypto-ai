import { expect, type Page } from '@playwright/test'

export const MOBILE_VIEWPORT = { width: 375, height: 812 }
export const TABLET_VIEWPORT = { width: 768, height: 1024 }
export const DESKTOP_VIEWPORT = { width: 1280, height: 800 }

const PRICE_PATTERN = /^\$\d{1,3}(,\d{3})*\.\d{2}$/

export function getPriceCard(page: Page) {
  return page.locator('[data-slot="card"]').filter({ hasText: 'BTC / USD' })
}

export function getPriceValue(page: Page) {
  return getPriceCard(page).getByText(PRICE_PATTERN).first()
}

export function getChangeStat(page: Page, label: string) {
  return page.getByRole('group', { name: label })
}

export async function expectPriceRendered(page: Page) {
  await expect(getPriceValue(page)).toBeVisible()
}

export async function expectChangeWindowsRendered(page: Page) {
  for (const label of ['24h change', '7d change']) {
    const stat = getChangeStat(page, label)
    await expect(stat).toBeVisible()
    await expect(stat).toContainText(/%/)
    await expect(stat).toContainText(/\$/)
  }
}

/** Nothing on the page may push the document wider than the viewport. */
export async function expectNoHorizontalScroll(page: Page) {
  const overflow = await page.evaluate(() => {
    const root = document.documentElement
    return root.scrollWidth - root.clientWidth
  })

  expect(overflow).toBeLessThanOrEqual(1)
}

/** Touch targets need to be tall enough to hit reliably on a phone. */
export async function expectTouchFriendlyChartControls(page: Page) {
  const button = page
    .getByRole('group', { name: 'Chart interval' })
    .getByRole('button')
    .first()

  const box = await button.boundingBox()
  expect(box?.height ?? 0).toBeGreaterThanOrEqual(40)
}

export async function expectPriceWithinViewport(page: Page) {
  const viewportWidth = page.viewportSize()?.width ?? 0
  const box = await getPriceValue(page).boundingBox()

  expect(box).not.toBeNull()
  expect((box?.x ?? 0) + (box?.width ?? 0)).toBeLessThanOrEqual(viewportWidth)
}
