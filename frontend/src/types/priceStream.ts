/** Transport state of the live price connection. */
export type PriceStreamStatus = 'connecting' | 'connected' | 'disconnected'

/**
 * The slice of socket behaviour the price stream depends on.
 * Narrow on purpose, so a real WebSocket and a simulated one are
 * interchangeable without stubbing the whole DOM interface.
 */
export type PriceSocketEvent =
  | { type: 'open' }
  | { type: 'message'; data: string }
  | { type: 'close' }
  | { type: 'error' }

export type PriceSocketHandle = {
  close: () => void
}

/** Opens a transport and pushes its events into `onEvent`. */
export type PriceSocketFactory = (
  onEvent: (event: PriceSocketEvent) => void,
) => PriceSocketHandle
