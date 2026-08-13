import { useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'
import { btcPriceSnapshotQueryKey } from '@/api/btcPrice'
import {
  parsePriceStreamMessage,
  reconnectDelayMs,
} from '@/components/dashboard/lib/priceStream'
import { createPriceSocket, priceStreamSource } from '@/lib/priceSocket'
import { usePriceStreamStore } from '@/stores/priceStreamStore'
import type { BtcPriceSnapshot } from '@/types/btcPrice'
import type { PriceSocketFactory, PriceSocketHandle } from '@/types/priceStream'

type UsePriceStreamOptions = {
  /** Injectable transport — defaults to the app's configured socket. */
  socketFactory?: PriceSocketFactory
}

/**
 * Keeps the price snapshot live off a socket, reconnecting with backoff when
 * the connection drops.
 *
 * Frames are written straight into the TanStack Query cache, so every consumer
 * of `useBtcPriceSnapshotQuery` re-renders immediately without prop drilling,
 * and the REST query stays as the fallback while the socket is down.
 */
export function usePriceStream({
  socketFactory,
}: UsePriceStreamOptions = {}) {
  const queryClient = useQueryClient()
  const status = usePriceStreamStore((state) => state.status)
  const lastUpdatedAt = usePriceStreamStore((state) => state.lastUpdatedAt)
  const setStatus = usePriceStreamStore((state) => state.setStatus)
  const setLastUpdatedAt = usePriceStreamStore((state) => state.setLastUpdatedAt)
  const reconnectAttempts = usePriceStreamStore(
    (state) => state.reconnectAttempts,
  )
  const setReconnectAttempts = usePriceStreamStore(
    (state) => state.setReconnectAttempts,
  )

  useEffect(() => {
    const factory = socketFactory ?? createPriceSocket()

    if (!factory) {
      setStatus('unavailable')
      return
    }

    const connect = factory

    let handle: PriceSocketHandle | undefined
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined
    let attempt = 0
    let isCancelled = false

    const applySnapshot = (snapshot: BtcPriceSnapshot) => {
      queryClient.setQueryData<BtcPriceSnapshot>(
        btcPriceSnapshotQueryKey(),
        snapshot,
      )
      setLastUpdatedAt(snapshot.updatedAt ?? new Date().toISOString())
    }

    const scheduleReconnect = () => {
      if (isCancelled) {
        return
      }

      attempt += 1
      setReconnectAttempts(attempt)
      setStatus('disconnected')
      reconnectTimer = setTimeout(open, reconnectDelayMs(attempt))
    }

    function open() {
      if (isCancelled) {
        return
      }

      setStatus(attempt === 0 ? 'connecting' : 'disconnected')

      handle = connect((event) => {
        if (isCancelled) {
          return
        }

        if (event.type === 'open') {
          attempt = 0
          setReconnectAttempts(0)
          setStatus('connected')
          return
        }

        if (event.type === 'message') {
          const snapshot = parsePriceStreamMessage(
            event.data,
            priceStreamSource(),
          )
          if (snapshot) {
            applySnapshot(snapshot)
          }
          return
        }

        // 'close' and 'error' both mean the stream stopped delivering.
        handle?.close()
        handle = undefined
        scheduleReconnect()
      })
    }

    open()

    return () => {
      isCancelled = true
      clearTimeout(reconnectTimer)
      handle?.close()
    }
  }, [
    queryClient,
    socketFactory,
    setStatus,
    setLastUpdatedAt,
    setReconnectAttempts,
  ])

  return { status, lastUpdatedAt, reconnectAttempts }
}
