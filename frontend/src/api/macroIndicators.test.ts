import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  MAIN_INDICATOR_NAMES,
  USE_MOCK_MACRO_INDICATORS,
  fetchMacroIndicators,
  fetchMacroIndicatorsFromApi,
  fetchMockMacroIndicators,
} from '@/api/macroIndicators'
import {
  makeIndicator,
  mockIndicatorsApiResponse,
} from '@/api/macroIndicators.testHelpers'

function mockFetchJson(body: unknown, init?: { ok?: boolean; statusText?: string }) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: init?.ok ?? true,
      statusText: init?.statusText ?? 'OK',
      json: async () => body,
    }),
  )
}

describe('fetchMacroIndicatorsFromApi', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('requests GET /api/v1/indicators', async () => {
    mockFetchJson(mockIndicatorsApiResponse)

    await fetchMacroIndicatorsFromApi()

    expect(fetch).toHaveBeenCalledWith('/api/v1/indicators')
  })

  it('keeps only CPI, Fed funds, and GDP using backend names', async () => {
    mockFetchJson(mockIndicatorsApiResponse)

    const indicators = await fetchMacroIndicatorsFromApi()

    expect(indicators.map((indicator) => indicator.indicator_name)).toEqual([
      'cpi',
      'federal_funds_rate',
      'gdp',
    ])
    expect(MAIN_INDICATOR_NAMES).toEqual([
      'cpi',
      'federal_funds_rate',
      'gdp',
    ])
  })

  it('matches indicator names case-insensitively', async () => {
    mockFetchJson({
      period: 'latest',
      count: 1,
      indicators: [
        makeIndicator({ indicator_name: 'CPI', current_value: 307.2 }),
      ],
    })

    const indicators = await fetchMacroIndicatorsFromApi()

    expect(indicators).toHaveLength(1)
    expect(indicators[0].indicator_name).toBe('CPI')
  })

  it('returns an empty list when the payload has no indicators', async () => {
    mockFetchJson({ period: 'latest', count: 0 })

    await expect(fetchMacroIndicatorsFromApi()).resolves.toEqual([])
  })

  it('throws when the indicators request fails', async () => {
    mockFetchJson({}, { ok: false, statusText: 'Internal Server Error' })

    await expect(fetchMacroIndicatorsFromApi()).rejects.toThrow(
      'Failed to fetch indicators: Internal Server Error',
    )
  })
})

describe('fetchMockMacroIndicators', () => {
  const MOCK_LATENCY_MS = 280

  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  async function fetchSettled() {
    const pending = fetchMockMacroIndicators()
    await vi.advanceTimersByTimeAsync(MOCK_LATENCY_MS)
    return pending
  }

  it('serves the main indicators without touching the network', async () => {
    vi.stubGlobal('fetch', vi.fn())

    const indicators = await fetchSettled()

    expect(indicators.map((indicator) => indicator.indicator_name)).toEqual([
      ...MAIN_INDICATOR_NAMES,
    ])
    expect(fetch).not.toHaveBeenCalled()
  })

  it('returns API-shaped indicators with trend and change data', async () => {
    const indicators = await fetchSettled()

    for (const indicator of indicators) {
      expect(indicator.time).toMatch(/^\d{4}-\d{2}-\d{2}T/)
      expect(Number.isFinite(indicator.current_value)).toBe(true)
      expect(['↑', '↓', '→']).toContain(indicator.trend)
    }
  })
})

describe('fetchMacroIndicators', () => {
  it('follows USE_MOCK_MACRO_INDICATORS', () => {
    expect(fetchMacroIndicators).toBe(
      USE_MOCK_MACRO_INDICATORS
        ? fetchMockMacroIndicators
        : fetchMacroIndicatorsFromApi,
    )
  })
})
