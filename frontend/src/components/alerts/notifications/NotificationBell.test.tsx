import { cleanup, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { resetSimulatedNotifications } from '@/api/alerts/simulatedNotifications'
import { simulateMarkAllAsRead } from '@/api/alerts/simulatedNotifications'
import { ALERTS_USER_ID } from '@/constants/alerts'
import {
  expectManageAlertsLink,
  expectNoUnreadBadge,
  expectReadBell,
  expectUnreadBadge,
  expectUnreadBell,
  getNotificationsButton,
  openNotifications,
  renderNotificationBell,
} from './NotificationBell.testHelpers'

vi.mock('@/hooks/alerts/useNotificationStream', () => ({
  useNotificationStream: () => ({
    status: 'unavailable',
    reconnectAttempts: 0,
  }),
}))

vi.mock('@/hooks/alerts/useToastUnreadNotifications', () => ({
  useToastUnreadNotifications: () => undefined,
}))

describe('NotificationBell', () => {
  beforeEach(() => {
    resetSimulatedNotifications()
  })

  afterEach(() => {
    cleanup()
  })

  it('opens the inbox without leaving the current page', async () => {
    const user = userEvent.setup()
    renderNotificationBell()

    expect(getNotificationsButton()).toBeInTheDocument()
    await openNotifications(user)

    expect(
      await screen.findByRole('heading', { name: /Notifications/ }),
    ).toBeInTheDocument()
    expect(await screen.findByText('3 unread')).toBeInTheDocument()
    expect(
      await screen.findByRole('button', { name: /BTC broke \$70,000/ }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /CPI print came in hot/ }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /BTC hit \$65,000/ }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /BTC dipped under \$60,000/ }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /24h outlook updated/ }),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Close' })).toBeInTheDocument()
    expectManageAlertsLink()
  })

  it('shows an unread count on the bell', async () => {
    renderNotificationBell()

    await waitFor(() => {
      expectUnreadBadge('3')
    })
    expectUnreadBell()
  })

  it('hides the unread badge when everything is read', async () => {
    await simulateMarkAllAsRead(ALERTS_USER_ID)
    renderNotificationBell()

    await waitFor(() => {
      expect(getNotificationsButton()).toBeInTheDocument()
    })
    expectNoUnreadBadge()
    expectReadBell()
  })
})
