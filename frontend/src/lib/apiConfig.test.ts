import { afterEach, describe, expect, it, vi } from 'vitest'
import { PRICE_ALERTS_PATH, BTC_PRICE_PATH } from '@/constants/apiUrls'
import {
  API_GATEWAY_BASE_URL,
  apiUrl,
  isApiGatewayConfigured,
  wsUrl,
} from '@/lib/apiConfig'

describe('apiConfig', () => {
  afterEach(() => {
    vi.unstubAllEnvs()
    vi.resetModules()
  })

  it('reports no backend in a frontend-only run', () => {
    // Pinned empty by the Vitest config, so a developer's local .env cannot
    // change this. Unset and empty both mean "no backend".
    expect(API_GATEWAY_BASE_URL).toBeFalsy()
    expect(isApiGatewayConfigured()).toBe(false)
    expect(apiUrl(BTC_PRICE_PATH)).toBeNull()
    expect(apiUrl(PRICE_ALERTS_PATH)).toBeNull()
    expect(wsUrl(BTC_PRICE_PATH)).toBeNull()
  })

  it('joins HTTP and WebSocket URLs to the gateway', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', 'http://localhost:8000/')
    vi.resetModules()

    const config = await import('@/lib/apiConfig')

    expect(config.isApiGatewayConfigured()).toBe(true)
    expect(config.apiUrl(BTC_PRICE_PATH)).toBe(
      `http://localhost:8000${BTC_PRICE_PATH}`,
    )
    expect(config.apiUrl(PRICE_ALERTS_PATH)).toBe(
      `http://localhost:8000${PRICE_ALERTS_PATH}`,
    )
    expect(config.wsUrl(BTC_PRICE_PATH)).toBe(
      `ws://localhost:8000${BTC_PRICE_PATH}`,
    )
  })

  it('uses a secure WebSocket when the gateway is https', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', 'https://api.example.com')
    vi.resetModules()

    const config = await import('@/lib/apiConfig')

    expect(config.wsUrl(BTC_PRICE_PATH)).toBe(
      `wss://api.example.com${BTC_PRICE_PATH}`,
    )
  })

  it('ignores a leftover alert-service host', async () => {
    vi.stubEnv('VITE_ALERT_API_BASE_URL', 'http://localhost:8003')
    vi.resetModules()

    const config = await import('@/lib/apiConfig')

    expect(config.isApiGatewayConfigured()).toBe(false)
    expect(config.apiUrl(PRICE_ALERTS_PATH)).toBeNull()
  })
})
