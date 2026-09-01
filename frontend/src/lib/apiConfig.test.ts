import { describe, expect, it } from 'vitest'
import {
  ALERT_API_BASE_URL,
  API_BASE_URL,
  NOTIFICATION_STREAM_URL,
  alertApiUrl,
  apiUrl,
  isAlertApiConfigured,
  isApiConfigured,
  isNotificationApiConfigured,
} from '@/lib/apiConfig'

describe('apiConfig', () => {
  it('reports no backend in a frontend-only run', () => {
    // Pinned empty by the Vitest config, so a developer's local .env cannot
    // change this. Unset and empty both mean "no backend".
    expect(API_BASE_URL).toBeFalsy()
    expect(isApiConfigured()).toBe(false)
    expect(apiUrl('/api/v1/btc/price')).toBeNull()
    expect(ALERT_API_BASE_URL).toBeFalsy()
    expect(isAlertApiConfigured()).toBe(false)
    expect(alertApiUrl('/api/v1/alerts/price')).toBeNull()
    expect(NOTIFICATION_STREAM_URL).toBeFalsy()
    expect(isNotificationApiConfigured()).toBe(false)
  })
})
