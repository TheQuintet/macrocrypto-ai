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

  it('uses the simulated socket when the gateway is unset', async () => {
    const { createPriceSocket, priceStreamSource } = await loadSocket()

    expect(createPriceSocket()).toBeTypeOf('function')
    expect(priceStreamSource()).toBe('simulated')
  })

  it('uses a live socket derived from the gateway base URL', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', 'http://localhost:8000')
    vi.resetModules()
    const { createPriceSocket, priceStreamSource } = await loadSocket()
    const { priceStreamUrl } = await import('@/constants/apiUrls')

    expect(createPriceSocket()).toBeTypeOf('function')
    expect(priceStreamSource()).toBe('live')
    expect(priceStreamUrl()).toBe('ws://localhost:8000/api/v1/btc/price/stream')
  })
})
