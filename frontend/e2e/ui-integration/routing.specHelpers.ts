import { expect, type Page } from '@playwright/test'
import { pageCopy, routes, type NavItemId } from '../../src/constants/navigation'

export async function goToRoute(page: Page, id: NavItemId) {
  await page.goto(routes[id])
}

export async function clickSidebarNav(page: Page, id: NavItemId) {
  await page.getByRole('link', { name: pageCopy[id].title }).click()
}

export async function openNotifications(page: Page) {
  await page.getByRole('button', { name: 'Notifications' }).click()
}

export async function clickManageAlerts(page: Page) {
  await page.getByRole('link', { name: 'Manage alerts' }).click()
}

export async function expectNotificationsOpen(page: Page) {
  await expect(
    page.getByRole('heading', { name: /Notifications/ }),
  ).toBeVisible()
}

export async function selectTimeRange(page: Page, range: string) {
  await page
    .getByRole('group', { name: 'Time range' })
    .getByRole('button', { name: range, exact: true })
    .click()
}

export async function expectRoute(page: Page, id: NavItemId) {
  const path = routes[id]
  const pattern =
    path === '/'
      ? /\/(?:\?.*)?$/
      : new RegExp(`${path.replace(/\//g, '\\/')}$`)
  await expect(page).toHaveURL(pattern)
}

/** The breadcrumb names the open page, so pages need no repeated heading. */
export async function expectCurrentPage(page: Page, id: NavItemId) {
  await expect(
    page
      .getByRole('navigation', { name: 'Breadcrumb' })
      .getByText(pageCopy[id].title, { exact: true }),
  ).toBeVisible()
}

export async function expectTimeRangeSelected(page: Page, range: string) {
  await expect(
    page
      .getByRole('group', { name: 'Time range' })
      .getByRole('button', { name: range, exact: true }),
  ).toHaveAttribute('aria-pressed', 'true')
}

export async function expectTimeRangeBadge(page: Page, range: string) {
  await expect(page.getByText(/showing data for/i)).toContainText(range)
}
