import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { unreadNotificationCountQueryKey } from '@/api/alerts/notifications'
import {
  NOTIFICATION_TOAST_DURATION_MS,
  showToast,
} from '@/components/alerts/shared/ToastNotification'
import { routes } from '@/constants/navigation'
import { NOTIFICATION_RECONNECT_BASE_DELAY_MS } from '@/lib/notificationStream'
import {
  advanceBy,
  createControllableNotificationSocket,
  expectStatus,
  getCachedNotifications,
  renderNotificationStream,
  seedNotificationCache,
  STREAM_NOTIFICATION,
} from '@/hooks/alerts/useNotificationStream.testHelpers'
import { resetNotificationStreamStore } from '@/stores/notificationStreamStore.testHelpers'

const navigate = vi.fn()
const markRead = vi.fn()

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>()
  return {
    ...actual,
    useNavigate: () => navigate,
  }
})

vi.mock('@/hooks/alerts/useMarkNotificationReadMutation', () => ({
  useMarkNotificationReadMutation: () => ({ mutate: markRead }),
}))

vi.mock('@/lib/notificationSocket', () => ({
  createNotificationSocket: () => null,
}))

vi.mock('@/components/alerts/shared/ToastNotification', async (importOriginal) => {
  const actual =
    await importOriginal<
      typeof import('@/components/alerts/shared/ToastNotification')
    >()
  return {
    ...actual,
    showToast: {
      info: vi.fn(),
      notification: vi.fn(),
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
    },
  }
})

describe('useNotificationStream', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    resetNotificationStreamStore()
    vi.mocked(showToast.notification).mockClear()
    navigate.mockClear()
    markRead.mockClear()
  })

  afterEach(() => {
    cleanup()
    vi.useRealTimers()
  })

  it('connects to the stream on mount', () => {
    const socket = createControllableNotificationSocket()
    const { view } = renderNotificationStream(socket.factory)

    expect(socket.connectCount()).toBe(1)
    expectStatus(view, 'connecting')
  })

  it('reports the connection once the socket opens', () => {
    const socket = createControllableNotificationSocket()
    const { view } = renderNotificationStream(socket.factory)

    socket.open()

    expectStatus(view, 'connected')
  })

  it('writes new alerts into the shared cache and toasts them', () => {
    const socket = createControllableNotificationSocket()
    const { queryClient } = renderNotificationStream(socket.factory)
    seedNotificationCache(queryClient)

    socket.open()
    socket.sendFrame()

    expect(getCachedNotifications(queryClient)?.notifications[0]?.id).toBe(
      STREAM_NOTIFICATION.id,
    )
    expect(
      queryClient.getQueryData<{ count: number }>(
        unreadNotificationCountQueryKey('user-1'),
      )?.count,
    ).toBe(1)
    expect(showToast.notification).toHaveBeenCalledWith(
      STREAM_NOTIFICATION.title,
      expect.stringContaining('Price alert'),
      expect.objectContaining({
        id: STREAM_NOTIFICATION.id,
        notificationType: 'price_alert',
        duration: NOTIFICATION_TOAST_DURATION_MS,
        onClick: expect.any(Function),
      }),
    )
    expect(showToast.notification).toHaveBeenCalledWith(
      STREAM_NOTIFICATION.title,
      expect.stringContaining('BTC/USD went above $72,000.00 at $72,140.00'),
      expect.objectContaining({ notificationType: 'price_alert' }),
    )
  })

  it('opens the matching page when the toast is clicked', () => {
    const socket = createControllableNotificationSocket()
    renderNotificationStream(socket.factory)

    socket.open()
    socket.sendFrame()

    const onClick = vi.mocked(showToast.notification).mock.calls[0]?.[2]
      ?.onClick
    onClick?.()

    expect(navigate).toHaveBeenCalledWith(routes.dashboard)
    expect(markRead).toHaveBeenCalledWith(STREAM_NOTIFICATION.id)
  })

  it('opens forecasts when a forecast toast is clicked', () => {
    const socket = createControllableNotificationSocket()
    renderNotificationStream(socket.factory)

    socket.open()
    socket.sendFrame({
      ...STREAM_NOTIFICATION,
      id: 'n-stream-forecast',
      notification_type: 'prediction_alert',
    })

    const onClick = vi.mocked(showToast.notification).mock.calls[0]?.[2]
      ?.onClick
    onClick?.()

    expect(navigate).toHaveBeenCalledWith(routes.forecasts)
  })

  it('does not replace an unloaded inbox with a single streamed alert', () => {
    const socket = createControllableNotificationSocket()
    const { queryClient } = renderNotificationStream(socket.factory)

    socket.open()
    socket.sendFrame()

    expect(getCachedNotifications(queryClient)).toBeUndefined()
    expect(showToast.notification).toHaveBeenCalledTimes(1)
  })

  it('ignores malformed frames without dropping the connection', () => {
    const socket = createControllableNotificationSocket()
    const { view, queryClient } = renderNotificationStream(socket.factory)
    seedNotificationCache(queryClient)

    socket.open()
    socket.sendFrame()
    socket.sendRaw('{ not json')

    expect(getCachedNotifications(queryClient)?.notifications).toHaveLength(1)
    expectStatus(view, 'connected')
  })

  it('does not toast a duplicate of an already cached alert', () => {
    const socket = createControllableNotificationSocket()
    const { queryClient } = renderNotificationStream(socket.factory)
    seedNotificationCache(queryClient)

    socket.open()
    socket.sendFrame()
    socket.sendFrame()

    expect(showToast.notification).toHaveBeenCalledTimes(1)
  })

  it('reconnects automatically after a connection loss', () => {
    const socket = createControllableNotificationSocket()
    const { view } = renderNotificationStream(socket.factory)

    socket.open()
    socket.drop()
    expect(socket.connectCount()).toBe(1)

    advanceBy(NOTIFICATION_RECONNECT_BASE_DELAY_MS)
    expect(socket.connectCount()).toBe(2)

    socket.open()
    expectStatus(view, 'connected')
  })

  it('reports the stream unavailable when there is no transport', () => {
    const { view } = renderNotificationStream(null)

    expectStatus(view, 'unavailable')
  })

  it('closes the socket and stops reconnecting on unmount', () => {
    const socket = createControllableNotificationSocket()
    const { view } = renderNotificationStream(socket.factory)

    socket.open()
    view.unmount()

    expect(socket.closeCount()).toBeGreaterThan(0)

    advanceBy(NOTIFICATION_RECONNECT_BASE_DELAY_MS * 10)
    expect(socket.connectCount()).toBe(1)
  })
})
