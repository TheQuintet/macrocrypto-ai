import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { resetSimulatedNotifications } from '@/api/alerts/simulatedNotifications'
import { createMockNotificationSocket } from '@/lib/mockNotificationSocket'
import { parseNotificationStreamMessage } from '@/lib/notificationStream'
import type { NotificationSocketEvent } from '@/types/notificationStream'

const OPEN_DELAY_MS = 10
const INTERVAL_MS = 100

function connect(emitIncoming = true) {
  const events: NotificationSocketEvent[] = []
  const factory = createMockNotificationSocket({
    userId: 'user-1',
    openDelayMs: OPEN_DELAY_MS,
    intervalMs: INTERVAL_MS,
    firstEmitMs: INTERVAL_MS,
    emitIncoming,
  })

  return { events, handle: factory((event) => events.push(event)) }
}

describe('createMockNotificationSocket', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    resetSimulatedNotifications()
  })

  afterEach(() => {
    vi.useRealTimers()
    resetSimulatedNotifications()
  })

  it('opens after the handshake delay without sending an immediate alert', () => {
    const { events } = connect()
    vi.advanceTimersByTime(OPEN_DELAY_MS)

    expect(events).toEqual([{ type: 'open' }])
  })

  it('emits the first alert after the first-emit delay', () => {
    const { events } = connect()
    vi.advanceTimersByTime(OPEN_DELAY_MS)
    expect(events.filter((event) => event.type === 'message')).toHaveLength(0)

    vi.advanceTimersByTime(INTERVAL_MS)
    expect(events.filter((event) => event.type === 'message')).toHaveLength(1)
  })

  it('pushes notification frames the stream can parse', () => {
    const { events } = connect()
    vi.advanceTimersByTime(OPEN_DELAY_MS + INTERVAL_MS)

    const frame = events[1]
    expect(frame?.type).toBe('message')
    const parsed = parseNotificationStreamMessage(
      frame?.type === 'message' ? frame.data : '',
    )
    expect(parsed?.notification_type).toBe('price_alert')
    expect(parsed?.read).toBe(false)
    expect(parsed?.data).toMatchObject({
      threshold_price: expect.any(Number),
      triggered_price: expect.any(Number),
    })
  })

  it('sends nothing more once closed by the caller', () => {
    const { events, handle } = connect()
    vi.advanceTimersByTime(OPEN_DELAY_MS)
    handle.close()
    vi.advanceTimersByTime(INTERVAL_MS * 5)

    expect(events).toEqual([{ type: 'open' }])
  })

  it('can open without inventing alerts', () => {
    const { events } = connect(false)
    vi.advanceTimersByTime(OPEN_DELAY_MS + INTERVAL_MS * 5)

    expect(events).toEqual([{ type: 'open' }])
  })
})
