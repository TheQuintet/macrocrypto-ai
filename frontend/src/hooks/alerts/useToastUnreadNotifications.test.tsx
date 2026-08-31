import { renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  NOTIFICATION_TOAST_DURATION_MS,
  showToast,
} from '@/components/alerts/shared/ToastNotification'
import { useToastUnreadNotifications } from '@/hooks/alerts/useToastUnreadNotifications'
import type { InAppNotification, NotificationResponse } from '@/types/alerts/notifications'

const markRead = vi.fn()

const unread: InAppNotification = {
  id: 'unread-1',
  user_id: 'user-1',
  alert_id: null,
  title: 'BTC broke $70,000',
  message: 'BTC/USD went above $70,000.00',
  notification_type: 'price_alert',
  data: null,
  action_url: '/',
  read: false,
  is_archived: false,
  created_at: '2026-08-31T12:00:00.000Z',
  read_at: null,
}

const read: InAppNotification = {
  ...unread,
  id: 'read-1',
  title: 'Already seen',
  read: true,
  read_at: unread.created_at,
}

const queryState = vi.hoisted(() => ({
  current: {
    data: undefined as NotificationResponse | undefined,
    isSuccess: false,
  },
}))

vi.mock('@/hooks/alerts/useMarkNotificationReadMutation', () => ({
  useMarkNotificationReadMutation: () => ({ mutate: markRead }),
}))

vi.mock('@/hooks/alerts/useNotificationsQuery', () => ({
  useNotificationsQuery: () => queryState.current,
}))

vi.mock('@/components/alerts/shared/ToastNotification', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('@/components/alerts/shared/ToastNotification')>()
  return {
    ...actual,
    showToast: {
      ...actual.showToast,
      notification: vi.fn(),
    },
  }
})

function renderToastUnread(notifications: InAppNotification[]) {
  queryState.current = {
    data: {
      total: notifications.length,
      limit: 50,
      offset: 0,
      notifications,
    },
    isSuccess: true,
  }

  return renderHook(() => useToastUnreadNotifications('user-1'), {
    wrapper: ({ children }: { children: ReactNode }) => (
      <MemoryRouter>{children}</MemoryRouter>
    ),
  })
}

describe('useToastUnreadNotifications', () => {
  beforeEach(() => {
    queryState.current = { data: undefined, isSuccess: false }
    vi.mocked(showToast.notification).mockClear()
    markRead.mockClear()
  })

  afterEach(() => {
    vi.mocked(showToast.notification).mockClear()
  })

  it('stacks every unread notification for two minutes', async () => {
    renderToastUnread([unread, read])

    await waitFor(() => {
      expect(showToast.notification).toHaveBeenCalledTimes(1)
    })
    expect(showToast.notification).toHaveBeenCalledWith(
      unread.title,
      expect.any(String),
      expect.objectContaining({
        id: unread.id,
        notificationType: 'price_alert',
        duration: NOTIFICATION_TOAST_DURATION_MS,
      }),
    )
  })

  it('does not toast the same unread list again on refetch', async () => {
    const view = renderToastUnread([unread])

    await waitFor(() => {
      expect(showToast.notification).toHaveBeenCalledTimes(1)
    })

    queryState.current = {
      data: {
        total: 2,
        limit: 50,
        offset: 0,
        notifications: [unread, { ...unread, id: 'unread-2', title: 'Newer' }],
      },
      isSuccess: true,
    }
    view.rerender()

    expect(showToast.notification).toHaveBeenCalledTimes(1)
  })
})
