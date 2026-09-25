import { isApiGatewayConfigured } from '@/lib/apiConfig'
import { createMockNotificationSocket } from '@/lib/mockNotificationSocket'
import type { NotificationSocketFactory } from '@/types/notificationStream'

/** Adapter over a real browser WebSocket. */
export function createWebSocketNotificationSocket(
  url: string,
): NotificationSocketFactory {
  return (onEvent) => {
    const socket = new WebSocket(url)

    socket.addEventListener('open', () => onEvent({ type: 'open' }))
    socket.addEventListener('message', (event: MessageEvent) =>
      onEvent({ type: 'message', data: String(event.data) }),
    )
    socket.addEventListener('close', () => onEvent({ type: 'close' }))
    socket.addEventListener('error', () => onEvent({ type: 'error' }))

    return {
      close: () => socket.close(),
    }
  }
}

/** Adapter over EventSource (SSE). */
export function createSseNotificationSocket(
  url: string,
): NotificationSocketFactory {
  return (onEvent) => {
    const source = new EventSource(url)

    source.addEventListener('open', () => onEvent({ type: 'open' }))
    source.addEventListener('message', (event: MessageEvent) =>
      onEvent({ type: 'message', data: String(event.data) }),
    )
    source.addEventListener('error', () => {
      source.close()
      onEvent({ type: 'error' })
    })

    return {
      close: () => source.close(),
    }
  }
}

/**
 * The gateway has no notification stream. With a gateway configured, the
 * inbox polls GET /api/v1/macro/notifications. Without one, the simulated
 * socket keeps the demo inbox moving.
 */
export function createNotificationSocket(
  userId: string,
): NotificationSocketFactory | null {
  if (isApiGatewayConfigured()) return null
  return createMockNotificationSocket({ userId })
}
