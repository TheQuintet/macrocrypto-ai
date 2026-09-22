import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { PredictionResponse } from '@/types/predictions'

const WIRE_RESPONSE: PredictionResponse = {
  horizon: '24h',
  model_name: 'prophet',
  confidence: 0.85,
  prediction_time: '2024-06-15T12:00:00.000Z',
  current_price: 63_500.42,
  predicted_end_price: 64_200.75,
  price_change_pct: 1.1,
  trend: 'up',
  predictions: [
    {
      time: '2024-06-15T13:00:00.000Z',
      predicted_price: 63_550.1,
      lower_bound: 63_400,
      upper_bound: 63_700.2,
    },
  ],
}

const PARAMS = { horizon: '24h', confidence: 0.85 } as const

function okResponse(body: unknown) {
  return vi.fn().mockResolvedValue({ ok: true, json: async () => body })
}

async function loadApi() {
  return import('@/api/predictions/btcPrediction')
}

describe('fetchBtcPrediction with a backend configured', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', 'http://localhost:8000')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  it('calls the prediction endpoint with horizon and confidence', async () => {
    const fetchSpy = okResponse(WIRE_RESPONSE)
    vi.stubGlobal('fetch', fetchSpy)
    const { fetchBtcPrediction } = await loadApi()

    await fetchBtcPrediction({ horizon: '7d', confidence: 0.95 })

    expect(fetchSpy).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/predict/btc?horizon=7d&confidence=0.95',
      { headers: { Accept: 'application/json' } },
    )
  })

  it('never sends `models`, which returns a different response envelope', async () => {
    const fetchSpy = okResponse(WIRE_RESPONSE)
    vi.stubGlobal('fetch', fetchSpy)
    const { fetchBtcPrediction } = await loadApi()

    await fetchBtcPrediction(PARAMS)

    expect(fetchSpy.mock.calls[0][0]).not.toContain('models=')
  })

  it('maps the real payload and marks it live', async () => {
    vi.stubGlobal('fetch', okResponse(WIRE_RESPONSE))
    const { fetchBtcPrediction } = await loadApi()

    const prediction = await fetchBtcPrediction(PARAMS)

    expect(prediction.source).toBe('live')
    expect(prediction.modelName).toBe('prophet')
    expect(prediction.predictedEndPrice).toBe(64_200.75)
    expect(prediction.points[0].upperBound).toBe(63_700.2)
  })

  it('throws instead of substituting invented forecasts when the service fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 404 }))
    const { fetchBtcPrediction } = await loadApi()

    await expect(fetchBtcPrediction(PARAMS)).rejects.toThrow(/404/)
  })

  it('propagates a network failure to the error state', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))
    const { fetchBtcPrediction } = await loadApi()

    await expect(fetchBtcPrediction(PARAMS)).rejects.toThrow('offline')
  })

  it('does not double up slashes on a trailing-slash base URL', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', 'http://localhost:8000/')
    vi.resetModules()
    const fetchSpy = okResponse(WIRE_RESPONSE)
    vi.stubGlobal('fetch', fetchSpy)
    const { fetchBtcPrediction } = await loadApi()

    await fetchBtcPrediction(PARAMS)

    expect(fetchSpy.mock.calls[0][0]).toBe(
      'http://localhost:8000/api/v1/predict/btc?horizon=24h&confidence=0.85',
    )
  })
})

describe('fetchBtcPrediction with no backend configured', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  it('falls back to simulated data and labels it as such', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)
    const { fetchBtcPrediction } = await loadApi()

    const prediction = await fetchBtcPrediction(PARAMS, Date.UTC(2024, 5, 15, 12))

    expect(fetchSpy).not.toHaveBeenCalled()
    expect(prediction.source).toBe('simulated')
    expect(prediction.points.length).toBeGreaterThan(0)
  })
})
