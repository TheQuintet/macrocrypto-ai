import { notificationStreamUrl } from '@/constants/apiUrls'
import { createMockNotificationSocket } from '@/lib/mockNotificationSocket'
import type { NotificationSocketFactory } from '@/types/notificationStream'

function withUserId(base: string, userId: string) {
  const separator = base.includes('?') ? '&' : '?'
  return `${base}${separator}user_id=${encodeURIComponent(userId)}`
}

function isWebSocketUrl(url: string) {
  return url.startsWith('ws://') || url.startsWith('wss://')
}

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
 * Live stream when the gateway is configured, otherwise the simulated push.
 */
export function createNotificationSocket(
  userId: string,
): NotificationSocketFactory {
  const streamUrl = notificationStreamUrl()
  if (streamUrl) {
    const url = withUserId(streamUrl, userId)
    return isWebSocketUrl(url)
      ? createWebSocketNotificationSocket(url)
      : createSseNotificationSocket(url)
  }

  return createMockNotificationSocket({ userId })
}
