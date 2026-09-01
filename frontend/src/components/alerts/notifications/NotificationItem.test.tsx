import { cleanup, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  buildSimulatedNotifications,
  resetSimulatedNotifications,
  simulatedNotificationIds,
} from '@/api/alerts/simulatedNotifications'
import { showToast } from '@/components/alerts/shared/ToastNotification'
import { routes } from '@/constants/navigation'
import {
  clickNotification,
  expectPath,
  renderNotificationItem,
} from './NotificationItem.testHelpers'

vi.mock('@/components/alerts/shared/ToastNotification', async (importOriginal) => {
  const actual =
    await importOriginal<
      typeof import('@/components/alerts/shared/ToastNotification')
    >()
  return {
    ...actual,
    showToast: {
      ...actual.showToast,
      dismiss: vi.fn(),
    },
  }
})

function notificationById(id: string) {
  const notification = buildSimulatedNotifications().find((item) => item.id === id)
  if (!notification) {
    throw new Error(`Missing simulated notification ${id}`)
  }
  return notification
}

describe('NotificationItem', () => {
  beforeEach(() => {
    resetSimulatedNotifications()
    vi.mocked(showToast.dismiss).mockClear()
  })

  afterEach(() => {
    cleanup()
  })

  it('shows type, payload, and timestamp like the toast', () => {
    const notification = notificationById(simulatedNotificationIds.breakout)
    renderNotificationItem(notification)

    expect(screen.getByText('Price alert')).toBeInTheDocument()
    expect(screen.getByText('BTC breakout')).toBeInTheDocument()
    expect(
      screen.getByText('BTC/USD went above $70,000.00 at $70,120.00'),
    ).toBeInTheDocument()
  })

  it('shows event impact on a macro inbox row', () => {
    const notification = notificationById(simulatedNotificationIds.cpiPrint)
    renderNotificationItem(notification)

    expect(screen.getByText('Macro alert')).toBeInTheDocument()
    expect(screen.getByText('CPI Release · high impact')).toBeInTheDocument()
    expect(
      screen.getByText(
        'August CPI rose 0.3%. Higher inflation is typically negative for BTC.',
      ),
    ).toBeInTheDocument()
  })

  it('shows horizon and confidence on a forecast inbox row', () => {
    const notification = notificationById(simulatedNotificationIds.forecast)
    renderNotificationItem(notification)

    expect(screen.getByText('Forecast alert')).toBeInTheDocument()
    expect(screen.getByText('24h · bullish · 58% confidence')).toBeInTheDocument()
    expect(
      screen.getByText('The model is leaning slightly bullish for the next 24 hours.'),
    ).toBeInTheDocument()
  })

  it('marks an unread price alert as read and opens the chart', async () => {
    const user = userEvent.setup()
    const notification = notificationById(simulatedNotificationIds.breakout)
    const { router } = renderNotificationItem(notification)

    expect(
      screen.getByRole('button', { name: `${notification.title} (unread)` }),
    ).toBeInTheDocument()

    await clickNotification(user, notification.title)

    expect(showToast.dismiss).toHaveBeenCalledWith(notification.id)
    expectPath(router, routes.dashboard)
  })

  it('opens the chart without waiting when the alert is already read', async () => {
    const user = userEvent.setup()
    const notification = notificationById(simulatedNotificationIds.dip)
    const { router } = renderNotificationItem(notification)

    await clickNotification(user, notification.title)

    expect(showToast.dismiss).toHaveBeenCalledWith(notification.id)
    expectPath(router, routes.dashboard)
  })

  it('opens the macro page from a macro indicator alert', async () => {
    const user = userEvent.setup()
    const notification = notificationById(simulatedNotificationIds.cpiPrint)
    const { router } = renderNotificationItem(notification)

    await clickNotification(user, notification.title)

    expectPath(router, routes.macro)
  })
})
