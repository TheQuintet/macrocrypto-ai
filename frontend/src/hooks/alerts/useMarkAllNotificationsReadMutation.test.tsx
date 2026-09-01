import { QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { notificationsQueryKey } from '@/api/alerts/notifications'
import { showToast } from '@/components/alerts/shared/ToastNotification'
import { useMarkAllNotificationsReadMutation } from '@/hooks/alerts/useMarkAllNotificationsReadMutation'
import { createTestQueryClient } from '@/test/renderWithQuery'
import type { InAppNotification, NotificationResponse } from '@/types/alerts/notifications'

vi.mock('@/api/alerts/notifications', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('@/api/alerts/notifications')>()
  return {
    ...actual,
    markAllNotificationsAsRead: vi.fn(async () => ({ count: 2 })),
  }
})

vi.mock('@/components/alerts/shared/ToastNotification', () => ({
  showToast: {
    dismissAll: vi.fn(),
  },
}))

const unread: InAppNotification = {
  id: 'unread-1',
  user_id: 'user-1',
  alert_id: null,
  title: 'BTC broke $70,000',
  message: 'Price alert',
  notification_type: 'price_alert',
  data: null,
  action_url: '/',
  read: false,
  is_archived: false,
  created_at: '2026-08-31T12:00:00.000Z',
  read_at: null,
}

describe('useMarkAllNotificationsReadMutation', () => {
  beforeEach(() => {
    vi.mocked(showToast.dismissAll).mockClear()
  })

  afterEach(() => {
    vi.mocked(showToast.dismissAll).mockClear()
  })

  it('closes every notification toast after marking all as read', async () => {
    const queryClient = createTestQueryClient()
    queryClient.setQueryData<NotificationResponse>(notificationsQueryKey('user-1'), {
      total: 1,
      limit: 50,
      offset: 0,
      notifications: [unread],
    })

    const { result } = renderHook(
      () => useMarkAllNotificationsReadMutation('user-1'),
      {
        wrapper: ({ children }: { children: ReactNode }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
      },
    )

    await act(async () => {
      result.current.mutate()
    })

    await waitFor(() => {
      expect(showToast.dismissAll).toHaveBeenCalledTimes(1)
    })
  })
})
