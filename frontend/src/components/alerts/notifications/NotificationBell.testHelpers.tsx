import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import type { UserEvent } from '@testing-library/user-event'
import { expect, vi } from 'vitest'
import { TooltipProvider } from '@/components/ui/tooltip'
import { ALERTS_USER_ID } from '@/constants/alerts'
import { routes } from '@/constants/navigation'
import { NotificationBell } from './NotificationBell'
import { useNotificationStore } from '@/stores/alerts/notificationStore'
import type { InAppNotification } from '@/types/alerts/priceAlert'

const snapshotStore = vi.mocked(useNotificationStore)

type StoreSnapshot = {
  notifications?: InAppNotification[]
  unreadCount?: number
  isLoading?: boolean
  error?: string | null
}

export function mockNotificationStore(overrides: StoreSnapshot = {}) {
  const fetchNotifications = vi.fn()
  const fetchUnreadCount = vi.fn()
  const markAsRead = vi.fn()
  const markAllAsRead = vi.fn()
  const clearError = vi.fn()

  snapshotStore.mockReturnValue({
    notifications: overrides.notifications ?? [],
    unreadCount: overrides.unreadCount ?? 0,
    isLoading: overrides.isLoading ?? false,
    error: overrides.error ?? null,
    fetchNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllAsRead,
    clearError,
  })

  return { fetchNotifications, fetchUnreadCount }
}

export function renderNotificationBell() {
  return render(
    <MemoryRouter>
      <TooltipProvider>
        <NotificationBell userId={ALERTS_USER_ID} />
      </TooltipProvider>
    </MemoryRouter>,
  )
}

export function getNotificationsButton() {
  return screen.getByRole('button', { name: 'Notifications' })
}

export async function openNotifications(user: UserEvent) {
  await user.click(getNotificationsButton())
}

export function expectManageAlertsLink() {
  expect(screen.getByRole('link', { name: 'Manage alerts' })).toHaveAttribute(
    'href',
    routes.alerts,
  )
}

export function expectUnreadBadge(count: string) {
  expect(screen.getByText(count)).toBeInTheDocument()
}

export function expectNoUnreadBadge() {
  expect(screen.queryByText('3')).not.toBeInTheDocument()
}
