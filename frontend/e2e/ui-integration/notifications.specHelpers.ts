import { expect, type Page } from '@playwright/test'

export async function openNotificationInbox(page: Page) {
  await page.getByRole('button', { name: 'Notifications' }).click()
}

export async function expectNotificationInboxOpen(page: Page) {
  await expect(
    page.getByRole('heading', { name: /Notifications/ }),
  ).toBeVisible()
}

export async function clickNotificationByTitle(page: Page, title: string) {
  await page.getByRole('dialog').getByRole('button', { name: title }).click()
}

export function notificationToastOpenButton(page: Page, title: string) {
  return page.getByRole('button', { name: `Open ${title}` })
}

export async function expectNotificationToastVisible(page: Page, title: string) {
  await expect(notificationToastOpenButton(page, title)).toBeVisible()
}

export async function expectNotificationToastHidden(page: Page, title: string) {
  await expect(notificationToastOpenButton(page, title)).toHaveCount(0)
}

export async function clickMarkAllNotificationsRead(page: Page) {
  await page.getByRole('button', { name: 'Mark all as read' }).click()
}

export function notificationsButton(page: Page) {
  return page.getByRole('button', { name: 'Notifications' })
}

export async function expectUnreadBadge(page: Page, count: string) {
  await expect(
    notificationsButton(page).getByText(count, { exact: true }),
  ).toBeVisible()
}

export async function expectNoUnreadBadge(page: Page, count: string) {
  await expect(
    notificationsButton(page).getByText(count, { exact: true }),
  ).toHaveCount(0)
}
