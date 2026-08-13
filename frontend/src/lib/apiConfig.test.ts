import { describe, expect, it } from 'vitest'
import { API_BASE_URL, apiUrl, isApiConfigured } from '@/lib/apiConfig'

describe('apiConfig', () => {
  it('reports no backend in a frontend-only run', () => {
    // Pinned empty by the Vitest config, so a developer's local .env cannot
    // change this. Unset and empty both mean "no backend".
    expect(API_BASE_URL).toBeFalsy()
    expect(isApiConfigured()).toBe(false)
    expect(apiUrl('/api/v1/btc/price')).toBeNull()
  })
})
