import { describe, expect, it } from 'vitest'
import { API_BASE_URL, apiUrl, isApiConfigured } from '@/lib/apiConfig'

describe('apiConfig', () => {
  it('reports no backend in a frontend-only run', () => {
    // Nothing sets VITE_API_BASE_URL under Vitest, which is the standalone case.
    expect(API_BASE_URL).toBeUndefined()
    expect(isApiConfigured()).toBe(false)
    expect(apiUrl('/api/v1/btc/price')).toBeNull()
  })
})
