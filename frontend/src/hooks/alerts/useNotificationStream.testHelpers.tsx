import { QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook } from '@testing-library/react'
import type { ReactNode } from 'react'
import { expect, vi } from 'vitest'
import { notificationsQueryKey } from '@/api/alerts/notifications'
import { useNotificationStream } from '@/hooks/alerts/useNotificationStream'
import { createTestQueryClient } from '@/test/renderWithQuery'
import type { InAppNotification, NotificationResponse } from '@/types/alerts/notifications'
import type {
  NotificationSocketEvent,
  NotificationSocketFactory,
} from '@/types/notificationStream'

export const STREAM_NOTIFICATION: InAppNotification = {
  id: 'n-stream-1',
  user_id: 'user-1',
  alert_id: null,
  title: 'BTC broke $72,000',
  message: 'BTC/USD went above $72,000.00',
  notification_type: 'price_alert',
  data: {
    name: 'BTC breakout',
    asset: 'BTC/USD',
    alert_type: 'crosses_above',
    threshold_price: 72_000,
    triggered_price: 72_140,
  },
  action_url: '/',
  read: false,
  is_archived: false,
  created_at: '2026-08-31T12:00:00.000Z',
  read_at: null,
}

export function createControllableNotificationSocket() {
  let emit: ((event: NotificationSocketEvent) => void) | undefined
  let connectCount = 0
  let closeCount = 0

  const factory: NotificationSocketFactory = (onEvent) => {
    connectCount += 1
    emit = onEvent
    return {
      close: () => {
        closeCount += 1
      },
    }
  }

  const send = (event: NotificationSocketEvent) => {
    act(() => {
      emit?.(event)
    })
  }

  return {
    factory,
    connectCount: () => connectCount,
    closeCount: () => closeCount,
    open: () => send({ type: 'open' }),
    sendFrame: (frame: unknown = STREAM_NOTIFICATION) =>
      send({ type: 'message', data: JSON.stringify(frame) }),
    sendRaw: (data: string) => send({ type: 'message', data }),
    drop: () => send({ type: 'close' }),
    fail: () => send({ type: 'error' }),
  }
}

export function renderNotificationStream(
  socketFactory: NotificationSocketFactory | null,
  userId = 'user-1',
) {
  const queryClient = createTestQueryClient()

  const view = renderHook(
    () => useNotificationStream(userId, { socketFactory }),
    {
      wrapper: ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      ),
    },
  )

  return { view, queryClient }
}

export function seedNotificationCache(
  queryClient: ReturnType<typeof createTestQueryClient>,
  notifications: InAppNotification[] = [],
  userId = 'user-1',
) {
  queryClient.setQueryData<NotificationResponse>(notificationsQueryKey(userId), {
    total: notifications.length,
    limit: 50,
    offset: 0,
    notifications,
  })
}

export function getCachedNotifications(
  queryClient: ReturnType<typeof createTestQueryClient>,
  userId = 'user-1',
) {
  return queryClient.getQueryData<NotificationResponse>(
    notificationsQueryKey(userId),
  )
}

export function advanceBy(ms: number) {
  act(() => {
    vi.advanceTimersByTime(ms)
  })
}

export function expectStatus(
  view: ReturnType<typeof renderNotificationStream>['view'],
  status: string,
) {
  expect(view.result.current.status).toBe(status)
}
