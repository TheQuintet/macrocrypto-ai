import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createMockPriceSocket } from '@/lib/mockPriceSocket'
import type { PriceSocketEvent } from '@/types/priceStream'

const OPEN_DELAY_MS = 10
const INTERVAL_MS = 100

function connect(framesBeforeDrop = 3) {
  const events: PriceSocketEvent[] = []
  const factory = createMockPriceSocket({
    openDelayMs: OPEN_DELAY_MS,
    intervalMs: INTERVAL_MS,
    framesBeforeDrop,
    now: () => Date.UTC(2024, 5, 15, 12, 0, 0),
  })

  return { events, handle: factory((event) => events.push(event)) }
}

describe('createMockPriceSocket', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('opens after the handshake delay and sends a first frame', () => {
    const { events } = connect()
    expect(events).toHaveLength(0)

    vi.advanceTimersByTime(OPEN_DELAY_MS)

    expect(events[0]).toEqual({ type: 'open' })
    expect(events[1].type).toBe('message')
  })

  it('sends frames the price stream can parse', () => {
    const { events } = connect()
    vi.advanceTimersByTime(OPEN_DELAY_MS)

    const frame = events[1]
    expect(frame.type).toBe('message')
    const payload = JSON.parse(frame.type === 'message' ? frame.data : '{}')
    expect(typeof payload.current_price).toBe('number')
    expect(typeof payload.change_7d_percent).toBe('number')
  })

  it('drops the connection after the configured number of frames', () => {
    const { events } = connect(3)
    vi.advanceTimersByTime(OPEN_DELAY_MS + INTERVAL_MS * 3)

    const messages = events.filter((event) => event.type === 'message')
    expect(messages).toHaveLength(3)
    expect(events.at(-1)).toEqual({ type: 'close' })
  })

  it('sends nothing more once closed by the caller', () => {
    const { events, handle } = connect()
    vi.advanceTimersByTime(OPEN_DELAY_MS)
    const countAtClose = events.length

    handle.close()
    vi.advanceTimersByTime(INTERVAL_MS * 5)

    expect(events).toHaveLength(countAtClose)
  })

  it('sends nothing when closed before the handshake completes', () => {
    const { events, handle } = connect()

    handle.close()
    vi.advanceTimersByTime(OPEN_DELAY_MS + INTERVAL_MS * 3)

    expect(events).toHaveLength(0)
  })
})
