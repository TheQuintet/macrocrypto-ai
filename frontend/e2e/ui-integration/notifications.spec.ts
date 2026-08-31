import { expect, test } from '@playwright/test'
import {
  expectPageHeading,
  expectRoute,
  goToRoute,
} from './routing.specHelpers'
import {
  clickMarkAllNotificationsRead,
  clickNotificationByTitle,
  expectNoUnreadBadge,
  expectNotificationInboxOpen,
  expectNotificationToastHidden,
  expectNotificationToastVisible,
  expectUnreadBadge,
  openNotificationInbox,
} from './notifications.specHelpers'

test.describe('in-app notifications UI integration', () => {
  test('unread badge opens an inbox sorted newest first', async ({ page }) => {
    await goToRoute(page, 'dashboard')

    await expectUnreadBadge(page, '3')
    await openNotificationInbox(page)
    await expectNotificationInboxOpen(page)

    const items = page.getByRole('listitem')
    await expect(items.first()).toContainText('BTC broke $70,000')
    await expect(items.first()).toContainText('Price alert')
    await expect(items.first()).toContainText(
      'BTC/USD went above $70,000.00 at $70,120.00',
    )
    await expect(items.nth(1)).toContainText('CPI print came in hot')
    await expect(items.nth(1)).toContainText('Macro alert')
    await expect(items.nth(1)).toContainText('CPI Release · high impact')
  })

  test('clicking a price alert opens the chart', async ({ page }) => {
    await goToRoute(page, 'alerts')

    await openNotificationInbox(page)
    await expectNotificationInboxOpen(page)
    await clickNotificationByTitle(page, 'BTC broke $70,000')

    await expectRoute(page, 'dashboard')
    await expectPageHeading(page, 'dashboard')
  })

  test('clicking an inbox row closes the matching toast', async ({ page }) => {
    await goToRoute(page, 'dashboard')

    await expectNotificationToastVisible(page, 'BTC broke $70,000')
    await expectNotificationToastVisible(page, 'CPI print came in hot')

    await openNotificationInbox(page)
    await expectNotificationInboxOpen(page)
    await clickNotificationByTitle(page, 'BTC broke $70,000')

    await expectNotificationToastHidden(page, 'BTC broke $70,000')
    await expectNotificationToastVisible(page, 'CPI print came in hot')
  })

  test('mark all as read clears the unread badge', async ({ page }) => {
    await goToRoute(page, 'dashboard')

    await expectUnreadBadge(page, '3')
    await openNotificationInbox(page)
    await clickMarkAllNotificationsRead(page)

    await expectNoUnreadBadge(page, '3')
  })

  test('clicking a macro alert opens macro indicators', async ({ page }) => {
    await goToRoute(page, 'alerts')

    await openNotificationInbox(page)
    await expectNotificationInboxOpen(page)
    await clickNotificationByTitle(page, 'CPI print came in hot')

    await expectRoute(page, 'macro')
    await expectPageHeading(page, 'macro')
  })
})
