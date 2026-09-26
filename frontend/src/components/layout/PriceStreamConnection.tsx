import { usePriceStream } from '@/hooks/usePriceStream'

/** Keeps the BTC price WebSocket open for the whole app shell. */
export function PriceStreamConnection() {
  usePriceStream()
  return null
}
