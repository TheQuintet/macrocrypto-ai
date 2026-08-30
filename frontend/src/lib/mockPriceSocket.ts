import { buildMockBtcPriceSnapshot } from '@/api/btcPrice/btcPrice'
import type { PriceSocketFactory } from '@/types/priceStream'

/** How often the simulated gateway pushes a frame. */
export const MOCK_STREAM_INTERVAL_MS = 2_000

/** Simulated connect handshake delay. */
export const MOCK_STREAM_OPEN_DELAY_MS = 120

/**
 * Frames pushed before the simulated connection drops. Exercises the
 * auto-reconnect path in dev without needing a server to fall over.
 */
export const MOCK_STREAM_FRAMES_BEFORE_DROP = 12

type MockPriceSocketOptions = {
  intervalMs?: number
  openDelayMs?: number
  framesBeforeDrop?: number
  now?: () => number
}

/**
 * Stands in for the gateway's price stream until the real route exists.
 * Speaks the same wire format, so swapping in a real socket changes nothing
 * downstream.
 */
export function createMockPriceSocket({
  intervalMs = MOCK_STREAM_INTERVAL_MS,
  openDelayMs = MOCK_STREAM_OPEN_DELAY_MS,
  framesBeforeDrop = MOCK_STREAM_FRAMES_BEFORE_DROP,
  now = () => Date.now(),
}: MockPriceSocketOptions = {}): PriceSocketFactory {
  return (onEvent) => {
    let isClosed = false
    let framesSent = 0
    let frameTimer: ReturnType<typeof setInterval> | undefined

    const stopFrames = () => {
      if (frameTimer !== undefined) {
        clearInterval(frameTimer)
        frameTimer = undefined
      }
    }

    const sendFrame = () => {
      if (isClosed) {
        return
      }

      onEvent({
        type: 'message',
        data: JSON.stringify(buildMockBtcPriceSnapshot(now())),
      })
      framesSent += 1

      if (framesSent >= framesBeforeDrop) {
        stopFrames()
        isClosed = true
        onEvent({ type: 'close' })
      }
    }

    const openTimer = setTimeout(() => {
      if (isClosed) {
        return
      }

      onEvent({ type: 'open' })
      sendFrame()
      frameTimer = setInterval(sendFrame, intervalMs)
    }, openDelayMs)

    return {
      close: () => {
        isClosed = true
        clearTimeout(openTimer)
        stopFrames()
      },
    }
  }
}
