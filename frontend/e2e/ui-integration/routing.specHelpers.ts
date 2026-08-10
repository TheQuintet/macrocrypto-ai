import { expect, type Page } from '@playwright/test'
import { pageCopy, routes, type NavItemId } from '../../src/constants/navigation'

export async function goToRoute(page: Page, id: NavItemId) {
  await page.goto(routes[id])
}

export async function clickSidebarNav(page: Page, id: Exclude<NavItemId, 'alerts'>) {
  await page.getByRole('link', { name: pageCopy[id].title }).click()
}

export async function selectTimeRange(page: Page, range: string) {
  await page.getByRole('button', { name: range, exact: true }).click()
}

export async function expectRoute(page: Page, id: NavItemId) {
  const path = routes[id]
  const pattern =
    path === '/'
      ? /\/(?:\?.*)?$/
      : new RegExp(`${path.replace(/\//g, '\\/')}$`)
  await expect(page).toHaveURL(pattern)
}

export async function expectPageHeading(page: Page, id: NavItemId) {
  await expect(
    page.getByRole('heading', { name: pageCopy[id].title, exact: true }),
  ).toBeVisible()
}

export async function expectTimeRangeSelected(page: Page, range: string) {
  await expect(
    page.getByRole('button', { name: range, exact: true }),
  ).toHaveAttribute('aria-pressed', 'true')
}

export async function expectTimeRangeBadge(page: Page, range: string) {
  await expect(page.getByText(/showing data for/i)).toContainText(range)
}
