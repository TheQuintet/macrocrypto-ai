import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  ALERT_API_BASE_URL,
  API_GATEWAY_BASE_URL,
  NOTIFICATION_STREAM_URL,
  alertApiUrl,
  apiUrl,
  isAlertApiConfigured,
  isApiConfigured,
  isNotificationApiConfigured,
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
    expect(isApiConfigured()).toBe(false)
    expect(apiUrl('/api/v1/btc/price')).toBeNull()
    expect(ALERT_API_BASE_URL).toBeFalsy()
    expect(isAlertApiConfigured()).toBe(false)
    expect(alertApiUrl('/api/v1/alerts/price')).toBeNull()
    expect(NOTIFICATION_STREAM_URL).toBeFalsy()
    expect(isNotificationApiConfigured()).toBe(false)
  })

  it('routes data and alert requests through the configured gateway', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', 'http://localhost:8000/')
    vi.stubEnv('VITE_ALERT_API_BASE_URL', 'http://localhost:8003')
    vi.resetModules()

    const config = await import('@/lib/apiConfig')

    expect(config.isApiConfigured()).toBe(true)
    expect(config.isAlertApiConfigured()).toBe(true)
    expect(config.apiUrl('/api/v1/btc/price')).toBe(
      'http://localhost:8000/api/v1/btc/price',
    )
    expect(config.alertApiUrl('/api/v1/alerts/price')).toBe(
      'http://localhost:8000/api/v1/alerts/price',
    )
  })
})
