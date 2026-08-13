import { createMockPriceSocket } from '@/lib/mockPriceSocket'
import type { PriceSource } from '@/types/btcPrice'
import type { PriceSocketFactory } from '@/types/priceStream'

/**
 * Gateway WebSocket URL, e.g. `wss://host/api/v1/btc/price/stream`.
 * Unset until the gateway exposes the route, which is when the simulated
 * socket below takes over.
 */
export const PRICE_STREAM_URL = import.meta.env.VITE_PRICE_WS_URL as
  | string
  | undefined

/** Whether the stream is a real socket or the simulated stand-in. */
export function priceStreamSource(): PriceSource {
  return PRICE_STREAM_URL ? 'live' : 'simulated'
}

/** Adapter over a real browser WebSocket. */
export function createWebSocketPriceSocket(url: string): PriceSocketFactory {
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

/**
 * The transport the app connects through: a real socket when a gateway URL is
 * configured, otherwise the simulated one.
 */
export function createPriceSocket(): PriceSocketFactory {
  if (PRICE_STREAM_URL) {
    return createWebSocketPriceSocket(PRICE_STREAM_URL)
  }

  return createMockPriceSocket()
}
