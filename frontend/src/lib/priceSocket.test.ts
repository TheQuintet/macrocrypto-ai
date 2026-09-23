import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

async function loadSocket() {
  return import('@/lib/priceSocket')
}

describe('createPriceSocket transport precedence', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.resetModules()
  })

  it('uses the simulated socket when nothing is configured', async () => {
    const { createPriceSocket } = await loadSocket()

    expect(createPriceSocket()).toBeTypeOf('function')
  })

  it('uses a real socket when a stream URL is configured', async () => {
    vi.stubEnv('VITE_PRICE_WS_URL', 'ws://localhost:8001/stream')
    vi.resetModules()
    const { createPriceSocket, priceStreamSource } = await loadSocket()

    expect(createPriceSocket()).toBeTypeOf('function')
    expect(priceStreamSource()).toBe('live')
  })

  it('refuses to simulate a stream over a real backend', async () => {
    // Both write the same query cache key, and a connected stream stands
    // polling down — so simulated frames would replace live prices entirely.
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', 'http://localhost:8000')
    vi.resetModules()
    const { createPriceSocket } = await loadSocket()

    expect(createPriceSocket()).toBeNull()
  })

  it('still uses a real stream when both are configured', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', 'http://localhost:8000')
    vi.stubEnv('VITE_PRICE_WS_URL', 'ws://localhost:8001/stream')
    vi.resetModules()
    const { createPriceSocket, priceStreamSource } = await loadSocket()

    expect(createPriceSocket()).toBeTypeOf('function')
    expect(priceStreamSource()).toBe('live')
  })
})
