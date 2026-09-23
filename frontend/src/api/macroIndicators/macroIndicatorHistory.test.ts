import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MAIN_INDICATOR_NAMES, MACRO_INDICATORS_MOCK_LATENCY_MS } from '@/api/macroIndicators/macroIndicatorsShared'
import { simulateMacroIndicatorHistory } from '@/api/macroIndicators/macroIndicatorHistory'
import { mockIndicatorsApiResponse } from '@/api/macroIndicators/macroIndicators.testHelpers'
import {
  groupIndicatorsByName,
  indexSeriesToBase100,
} from '@/lib/macroIndicatorHistory'

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
  return import('@/api/macroIndicators/macroIndicatorHistory')
}

describe('macroIndicatorHistoryQueryKey', () => {
  it('keys history by selected timeframe', async () => {
    const { macroIndicatorHistoryQueryKey } = await loadApi()

    expect(macroIndicatorHistoryQueryKey('90d')).toEqual([
      'macro-indicator-history',
      '90d',
    ])
  })
})

describe('fetchMacroIndicatorHistory with a backend configured', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', 'http://localhost:8000')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  it('requests GET /api/v1/indicators?period= for the selected window', async () => {
    mockFetchJson(mockIndicatorsApiResponse)
    const { fetchMacroIndicatorHistory } = await loadApi()

    await fetchMacroIndicatorHistory('90d')

    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/indicators?period=90d',
      { headers: { Accept: 'application/json' } },
    )
  })

  it('requests the selected window without client-side clipping', async () => {
    mockFetchJson(mockIndicatorsApiResponse)
    const { fetchMacroIndicatorHistory } = await loadApi()

    await fetchMacroIndicatorHistory('30d')

    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/indicators?period=30d',
      { headers: { Accept: 'application/json' } },
    )
  })

  it('throws instead of substituting fake series when the service fails', async () => {
    mockFetchJson({}, { ok: false, status: 503 })
    const { fetchMacroIndicatorHistory } = await loadApi()

    await expect(fetchMacroIndicatorHistory('1y')).rejects.toThrow(/503/)
  })

  it('calls the gateway history endpoint for the selected timeframe', async () => {
    mockFetchJson(mockIndicatorsApiResponse)
    const { fetchMacroIndicatorHistory } = await loadApi()

    await fetchMacroIndicatorHistory('5y')

    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/indicators?period=5y',
      { headers: { Accept: 'application/json' } },
    )
  })

  it('marks live history as live', async () => {
    mockFetchJson(mockIndicatorsApiResponse)
    const { fetchMacroIndicatorHistory } = await loadApi()

    const indicators = await fetchMacroIndicatorHistory('90d')

    expect(indicators.every((indicator) => indicator.dataSource === 'live')).toBe(
      true,
    )
  })
})

describe('simulateMacroIndicatorHistory', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('serves a multi-point series for a historical period', async () => {
    const pending = simulateMacroIndicatorHistory('30d')
    await vi.advanceTimersByTimeAsync(MACRO_INDICATORS_MOCK_LATENCY_MS)
    const indicators = await pending

    const names = new Set(indicators.map((item) => item.indicator_name))
    expect([...names]).toEqual([...MAIN_INDICATOR_NAMES])
    expect(indicators.length).toBeGreaterThan(MAIN_INDICATOR_NAMES.length)
  })

  it('keeps CPI, Fed funds, and GDP on distinct rebased paths', async () => {
    const pending = simulateMacroIndicatorHistory('1y')
    await vi.advanceTimersByTimeAsync(MACRO_INDICATORS_MOCK_LATENCY_MS)
    const series = groupIndicatorsByName(await pending)
    const indexed = series.map((item) =>
      indexSeriesToBase100(item.points).map((point) => point.value),
    )

    expect(series.map((item) => item.name)).toEqual([...MAIN_INDICATOR_NAMES])

    for (let left = 0; left < indexed.length; left += 1) {
      for (let right = left + 1; right < indexed.length; right += 1) {
        const maxDiff = Math.max(
          ...indexed[left].map((value, index) =>
            Math.abs(value - indexed[right][index]),
          ),
        )
        expect(maxDiff).toBeGreaterThan(2)
      }
    }
  })

  it('labels simulated history so it cannot pass as live FRED prints', async () => {
    const pending = simulateMacroIndicatorHistory('30d')
    await vi.advanceTimersByTimeAsync(MACRO_INDICATORS_MOCK_LATENCY_MS)
    const indicators = await pending

    expect(
      indicators.every((indicator) => indicator.dataSource === 'simulated'),
    ).toBe(true)
  })
})

describe('fetchMacroIndicatorHistory with no backend configured', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  it('falls back to simulated series and does not touch the network', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)
    const { fetchMacroIndicatorHistory } = await loadApi()

    const pending = fetchMacroIndicatorHistory('30d')
    await vi.advanceTimersByTimeAsync(MACRO_INDICATORS_MOCK_LATENCY_MS)
    const indicators = await pending

    expect(fetchSpy).not.toHaveBeenCalled()
    expect(indicators.length).toBeGreaterThan(MAIN_INDICATOR_NAMES.length)
    expect(
      indicators.every((indicator) => indicator.dataSource === 'simulated'),
    ).toBe(true)
  })
})
