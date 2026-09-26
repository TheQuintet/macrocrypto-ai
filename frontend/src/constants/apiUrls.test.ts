import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  NOTIFICATIONS_STREAM_PATH,
  PRICE_ALERTS_PATH,
  PRICE_STREAM_PATH,
  notificationStreamUrl,
  priceStreamUrl,
  unusedApiPaths,
} from '@/constants/apiUrls'

describe('apiUrls', () => {
  afterEach(() => {
    vi.unstubAllEnvs()
    vi.resetModules()
  })

  it('keeps alert paths on the gateway', () => {
    expect(PRICE_ALERTS_PATH).toBe('/api/v1/alerts/price')
  })

  it('lists unused OpenAPI paths by service', () => {
    expect(unusedApiPaths.dataService).toEqual([
      '/api/v1/btc/dominance',
      '/api/v1/btc/status',
      '/api/v1/regimes/btc',
      '/api/v1/regimes/{regime_id}',
    ])
    expect(unusedApiPaths.alertService).toEqual([
      '/api/v1/alerts/prediction/config/{user_id}',
      '/api/v1/macro/subscribe/{user_id}/{event_type}',
      '/api/v1/macro/subscribe-all/{user_id}',
      '/api/v1/macro/unsubscribe-all/{user_id}',
      '/api/v1/macro/alerts',
      '/api/v1/macro/alerts/{user_id}',
      '/api/v1/macro/alerts/{alert_id}',
      '/api/v1/macro/notifications/{notification_id}/read',
      '/api/v1/macro/events/upcoming',
    ])
    expect(unusedApiPaths.aiService).toEqual([
      '/api/v1/performance/btc',
      '/api/v1/correlation/btc',
      '/api/v1/exports/{file_name}',
      '/api/v1/methodology',
      '/api/v1/methodology/versions',
      '/api/v1/methodology/changelog',
      '/api/v1/events/historical',
    ])
  })

  it('leaves stream URLs unset when the gateway is unset', () => {
    expect(priceStreamUrl()).toBeNull()
    expect(notificationStreamUrl()).toBeNull()
  })

  it('builds stream URLs from the gateway plus the path', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', 'http://localhost:8000/')
    vi.resetModules()

    const urls = await import('@/constants/apiUrls')

    expect(urls.priceStreamUrl()).toBe(`ws://localhost:8000${PRICE_STREAM_PATH}`)
    expect(urls.notificationStreamUrl()).toBe(
      `http://localhost:8000${NOTIFICATIONS_STREAM_PATH}`,
    )
    expect(urls.priceStreamUrl()).not.toContain('user_id')
  })
})
