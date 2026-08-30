import { cleanup, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ALERTS_USER_ID } from '@/constants/alerts'
import { useNotificationStore } from '@/stores/alerts/notificationStore'
import {
  expectManageAlertsLink,
  expectNoUnreadBadge,
  expectUnreadBadge,
  getNotificationsButton,
  mockNotificationStore,
  openNotifications,
  renderNotificationBell,
} from './NotificationBell.testHelpers'

vi.mock('@/stores/alerts/notificationStore', () => ({
  useNotificationStore: vi.fn(),
}))

describe('NotificationBell', () => {
  beforeEach(() => {
    vi.mocked(useNotificationStore).mockReset()
  })

  afterEach(() => {
    cleanup()
  })

  it('opens the inbox without leaving the current page', async () => {
    const user = userEvent.setup()
    const { fetchNotifications } = mockNotificationStore()
    renderNotificationBell()

    expect(getNotificationsButton()).toBeInTheDocument()
    await openNotifications(user)

    expect(screen.getByRole('heading', { name: 'Notifications' })).toBeInTheDocument()
    expectManageAlertsLink()
    expect(fetchNotifications).toHaveBeenCalledWith(ALERTS_USER_ID)
  })

  it('shows an unread count on the bell', () => {
    mockNotificationStore({ unreadCount: 3 })
    renderNotificationBell()

    expectUnreadBadge('3')
  })

  it('hides the unread badge when everything is read', () => {
    mockNotificationStore({ unreadCount: 0 })
    renderNotificationBell()

    expectNoUnreadBadge()
  })
})
