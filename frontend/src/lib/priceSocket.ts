import { priceStreamUrl } from '@/constants/apiUrls'
import { isApiGatewayConfigured } from '@/lib/apiConfig'
import { createMockPriceSocket } from '@/lib/mockPriceSocket'
import type { PriceSource } from '@/types/btcPrice'
import type { PriceSocketFactory } from '@/types/priceStream'

/** Whether the stream is a real socket or the simulated stand-in. */
export function priceStreamSource(): PriceSource {
  return isApiGatewayConfigured() ? 'live' : 'simulated'
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
 * The transport the app connects through.
 *
 * Gateway set → live socket at the derived gateway path. Unset → simulated
 * stand-in. The simulated socket must never run on top of a real backend:
 * both write the same query cache key, so simulated frames would overwrite
 * live prices.
 */
export function createPriceSocket(): PriceSocketFactory {
  const url = priceStreamUrl()
  if (url) {
    return createWebSocketPriceSocket(url)
  }

  return createMockPriceSocket()
}
