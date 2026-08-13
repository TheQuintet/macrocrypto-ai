import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { RECONNECT_BASE_DELAY_MS } from '@/components/dashboard/lib/priceStream'
import {
  advanceBy,
  createControllableSocket,
  expectStatus,
  getCachedSnapshot,
  PRICE_FRAME,
  renderPriceStream,
} from '@/hooks/usePriceStream.testHelpers'
import { resetPriceStreamStore } from '@/stores/priceStreamStore.testHelpers'

// Tests inject their own transport; stub the default so "no transport
// configured" is reachable without stubbing env and reloading modules.
vi.mock('@/lib/priceSocket', () => ({
  createPriceSocket: () => null,
  priceStreamSource: () => 'simulated',
}))

describe('usePriceStream', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    resetPriceStreamStore()
  })

  afterEach(() => {
    cleanup()
    vi.useRealTimers()
  })

  it('connects to the stream on mount', () => {
    const socket = createControllableSocket()
    const { view } = renderPriceStream(socket.factory)

    expect(socket.connectCount()).toBe(1)
    expectStatus(view, 'connecting')
  })

  it('reports the connection once the socket opens', () => {
    const socket = createControllableSocket()
    const { view } = renderPriceStream(socket.factory)

    socket.open()

    expectStatus(view, 'connected')
  })

  it('renders price updates immediately into the shared cache', () => {
    const socket = createControllableSocket()
    const { view, queryClient } = renderPriceStream(socket.factory)

    socket.open()
    socket.sendFrame()

    expect(getCachedSnapshot(queryClient)?.currentPrice).toBe(64_213.5)
    expect(view.result.current.lastUpdatedAt).toBe(PRICE_FRAME.updated_at)
  })

  it('keeps applying each new frame as it arrives', () => {
    const socket = createControllableSocket()
    const { queryClient } = renderPriceStream(socket.factory)

    socket.open()
    socket.sendFrame()
    socket.sendFrame({ ...PRICE_FRAME, current_price: 65_000 })

    expect(getCachedSnapshot(queryClient)?.currentPrice).toBe(65_000)
  })

  it('ignores malformed frames without dropping the connection', () => {
    const socket = createControllableSocket()
    const { view, queryClient } = renderPriceStream(socket.factory)

    socket.open()
    socket.sendFrame()
    socket.sendRaw('{ not json')

    expect(getCachedSnapshot(queryClient)?.currentPrice).toBe(64_213.5)
    expectStatus(view, 'connected')
  })

  it('reports a disconnection when the socket closes', () => {
    const socket = createControllableSocket()
    const { view } = renderPriceStream(socket.factory)

    socket.open()
    socket.drop()

    expectStatus(view, 'disconnected')
  })

  it('reconnects automatically after a connection loss', () => {
    const socket = createControllableSocket()
    const { view } = renderPriceStream(socket.factory)

    socket.open()
    socket.drop()
    expect(socket.connectCount()).toBe(1)

    advanceBy(RECONNECT_BASE_DELAY_MS)
    expect(socket.connectCount()).toBe(2)

    socket.open()
    expectStatus(view, 'connected')
  })

  it('backs off further when a reconnect attempt also fails', () => {
    const socket = createControllableSocket()
    renderPriceStream(socket.factory)

    socket.open()
    socket.drop()
    advanceBy(RECONNECT_BASE_DELAY_MS)
    expect(socket.connectCount()).toBe(2)

    socket.drop()
    advanceBy(RECONNECT_BASE_DELAY_MS)
    expect(socket.connectCount()).toBe(2)

    advanceBy(RECONNECT_BASE_DELAY_MS)
    expect(socket.connectCount()).toBe(3)
  })

  it('treats a socket error as a connection loss', () => {
    const socket = createControllableSocket()
    const { view } = renderPriceStream(socket.factory)

    socket.open()
    socket.fail()

    expectStatus(view, 'disconnected')
    advanceBy(RECONNECT_BASE_DELAY_MS)
    expect(socket.connectCount()).toBe(2)
  })

  it('reports the stream unavailable when there is no transport', () => {
    const { view } = renderPriceStream(null)

    expectStatus(view, 'unavailable')
  })

  it('closes the socket and stops reconnecting on unmount', () => {
    const socket = createControllableSocket()
    const { view } = renderPriceStream(socket.factory)

    socket.open()
    view.unmount()

    expect(socket.closeCount()).toBeGreaterThan(0)

    advanceBy(RECONNECT_BASE_DELAY_MS * 10)
    expect(socket.connectCount()).toBe(1)
  })
})
