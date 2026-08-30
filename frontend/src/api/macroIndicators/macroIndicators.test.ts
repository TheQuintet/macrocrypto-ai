import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  MAIN_INDICATOR_NAMES,
  simulateMacroIndicators,
} from '@/api/macroIndicators/macroIndicators'
import { MACRO_INDICATORS_MOCK_LATENCY_MS } from '@/api/macroIndicators/macroIndicatorsShared'
import {
  makeIndicator,
  mockIndicatorsApiResponse,
} from '@/api/macroIndicators/macroIndicators.testHelpers'

function mockFetchJson(
  body: unknown,
  init?: { ok?: boolean; status?: number; statusText?: string },
) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: init?.ok ?? true,
      status: init?.status ?? 200,
      statusText: init?.statusText ?? 'OK',
      json: async () => body,
    }),
  )
}

async function loadApi() {
  return import('@/api/macroIndicators/macroIndicators')
}

describe('simulateMacroIndicators', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  async function simulateSettled() {
    const pending = simulateMacroIndicators()
    await vi.advanceTimersByTimeAsync(MACRO_INDICATORS_MOCK_LATENCY_MS)
    return pending
  }

  it('serves the main indicators without touching the network', async () => {
    vi.stubGlobal('fetch', vi.fn())

    const indicators = await simulateSettled()

    expect(indicators.map((indicator) => indicator.indicator_name)).toEqual([
      ...MAIN_INDICATOR_NAMES,
    ])
    expect(fetch).not.toHaveBeenCalled()
  })

  it('returns API-shaped indicators labelled as simulated', async () => {
    const indicators = await simulateSettled()

    for (const indicator of indicators) {
      expect(indicator.time).toMatch(/^\d{4}-\d{2}-\d{2}T/)
      expect(Number.isFinite(indicator.current_value)).toBe(true)
      expect(['↑', '↓', '→']).toContain(indicator.trend)
      expect(indicator.dataSource).toBe('simulated')
    }
  })
})

describe('fetchMacroIndicators with a backend configured', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:8001')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  it('calls the data service indicators endpoint', async () => {
    mockFetchJson(mockIndicatorsApiResponse)
    const { fetchMacroIndicators } = await loadApi()

    await fetchMacroIndicators()

    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8001/api/v1/indicators',
      { headers: { Accept: 'application/json' } },
    )
  })

  it('keeps only CPI, Fed funds, and GDP using backend names', async () => {
    mockFetchJson(mockIndicatorsApiResponse)
    const { fetchMacroIndicators } = await loadApi()

    const indicators = await fetchMacroIndicators()

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
    const { fetchMacroIndicators } = await loadApi()

    const indicators = await fetchMacroIndicators()

    expect(indicators).toHaveLength(1)
    expect(indicators[0].indicator_name).toBe('CPI')
  })

  it('returns an empty list when the payload has no indicators', async () => {
    mockFetchJson({ period: 'latest', count: 0 })
    const { fetchMacroIndicators } = await loadApi()

    await expect(fetchMacroIndicators()).resolves.toEqual([])
  })

  it('maps the payload and marks it live', async () => {
    mockFetchJson(mockIndicatorsApiResponse)
    const { fetchMacroIndicators } = await loadApi()

    const indicators = await fetchMacroIndicators()

    expect(indicators.every((indicator) => indicator.dataSource === 'live')).toBe(
      true,
    )
  })

  it('throws instead of substituting fake indicators when the service fails', async () => {
    mockFetchJson({}, { ok: false, status: 503 })
    const { fetchMacroIndicators } = await loadApi()

    await expect(fetchMacroIndicators()).rejects.toThrow(/503/)
  })
})

describe('fetchMacroIndicators with no backend configured', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  it('falls back to simulated data and does not touch the network', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)
    const { fetchMacroIndicators, MAIN_INDICATOR_NAMES } = await loadApi()

    const pending = fetchMacroIndicators()
    await vi.advanceTimersByTimeAsync(MACRO_INDICATORS_MOCK_LATENCY_MS)
    const indicators = await pending

    expect(fetchSpy).not.toHaveBeenCalled()
    expect(indicators.map((indicator) => indicator.indicator_name)).toEqual([
      ...MAIN_INDICATOR_NAMES,
    ])
    expect(
      indicators.every((indicator) => indicator.dataSource === 'simulated'),
    ).toBe(true)
  })
})
