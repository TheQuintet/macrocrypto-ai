import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  historyParamsFor,
  mapPredictionHistory,
  predictionHistoryQueryKey,
} from '@/api/predictions/predictionHistory'
import { buildSimulatedHistoryPoints } from '@/api/predictions/simulatedPredictionHistory'
import { HISTORY_WINDOW } from '@/api/predictions/predictionWindow'
import type { PredictionHistoryResponse } from '@/types/predictions'

const FIXED_NOW_MS = Date.UTC(2024, 5, 15, 12, 0, 0)
const HOUR_MS = 60 * 60 * 1000
const ANCHOR = 64_000

const WIRE_RESPONSE: PredictionHistoryResponse = {
  range: '24h',
  interval: '1h',
  points: [
    {
      timestamp: '2024-06-15T11:00:00.000Z',
      open: 63_000,
      high: 63_400,
      low: 62_900,
      close: 63_200,
    },
  ],
}

describe('historyParamsFor', () => {
  it('fetches a week of hourly candles behind the 24h forecast', () => {
    expect(historyParamsFor('24h')).toEqual({
      horizon: '24h',
      range: '7d',
      interval: '1h',
    })
  })

  it('fetches a month of hourly candles behind the 7d forecast', () => {
    expect(historyParamsFor('7d')).toEqual({
      horizon: '7d',
      range: '30d',
      interval: '1h',
    })
  })
})

describe('predictionHistoryQueryKey', () => {
  it('keys on the window, not the confidence — the past does not move', () => {
    expect(
      predictionHistoryQueryKey({
        horizon: '24h',
        range: '24h',
        interval: '1h',
      }),
    ).toEqual([
      'btc-prediction-history',
      '24h',
      '1h',
    ])
  })
})

describe('mapPredictionHistory', () => {
  it('camel-cases the service payload into chart candles', () => {
    const history = mapPredictionHistory(
      WIRE_RESPONSE,
      historyParamsFor('24h'),
      'live',
    )

    expect(history.source).toBe('live')
    expect(history.candles).toEqual([
      {
        time: '2024-06-15T11:00:00.000Z',
        timeMs: Date.UTC(2024, 5, 15, 11),
        open: 63_000,
        high: 63_400,
        low: 62_900,
        close: 63_200,
      },
    ])
  })

  it('survives an empty batch from the service', () => {
    const history = mapPredictionHistory(
      { ...WIRE_RESPONSE, points: [] },
      historyParamsFor('7d'),
    )

    expect(history.candles).toEqual([])
  })
})

describe('buildSimulatedHistoryPoints', () => {
  it('builds the full fetched window, not just what is shown at rest', () => {
    expect(
      buildSimulatedHistoryPoints(
        historyParamsFor('24h'),
        FIXED_NOW_MS,
        ANCHOR,
      ),
    ).toHaveLength(HISTORY_WINDOW['24h'].candles)
    expect(
      buildSimulatedHistoryPoints(
        historyParamsFor('7d'),
        FIXED_NOW_MS,
        ANCHOR,
      ),
    ).toHaveLength(HISTORY_WINDOW['7d'].candles)
  })

  it('is deterministic for a moment in time', () => {
    const params = historyParamsFor('24h')

    expect(buildSimulatedHistoryPoints(params, FIXED_NOW_MS, ANCHOR)).toEqual(
      buildSimulatedHistoryPoints(params, FIXED_NOW_MS, ANCHOR),
    )
  })

  it('lands its final close on the anchor the forecast departs from', () => {
    const points = buildSimulatedHistoryPoints(
      historyParamsFor('24h'),
      FIXED_NOW_MS,
      ANCHOR,
    )

    expect(points[points.length - 1].close).toBeCloseTo(ANCHOR, 1)
  })

  it('keeps every candle well formed', () => {
    const points = buildSimulatedHistoryPoints(
      historyParamsFor('7d'),
      FIXED_NOW_MS,
      ANCHOR,
    )

    for (const point of points) {
      expect(point.high).toBeGreaterThanOrEqual(Math.max(point.open, point.close))
      expect(point.low).toBeLessThanOrEqual(Math.min(point.open, point.close))
    }
  })

  it('spaces the 7d history hourly, like the forecast it sits behind', () => {
    const times = buildSimulatedHistoryPoints(
      historyParamsFor('7d'),
      FIXED_NOW_MS,
      ANCHOR,
    ).map((point) => new Date(point.timestamp).getTime())

    expect(
      times.slice(1).every((time, index) => time - times[index] === HOUR_MS),
    ).toBe(true)
  })

  /**
   * The data service stamps a candle at its open time. The newest simulated
   * candle opened an hour before now and closed on the anchor at now.
   */
  it('stamps each candle at its open time, the newest an hour before now', () => {
    const points = buildSimulatedHistoryPoints(
      historyParamsFor('24h'),
      FIXED_NOW_MS,
      ANCHOR,
    )
    const candles = HISTORY_WINDOW['24h'].candles

    expect(points[points.length - 1].timestamp).toBe(
      new Date(FIXED_NOW_MS - HOUR_MS).toISOString(),
    )
    expect(points[0].timestamp).toBe(
      new Date(FIXED_NOW_MS - candles * HOUR_MS).toISOString(),
    )
  })
})

describe('fetchPredictionHistory', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  /**
   * max_points=0 stops the service merging the 720 hourly candles behind a
   * 7d forecast into two-hour ones under its default 500-point cap.
   */
  it('calls the gateway-proxied history route uncapped, at the asked interval', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', 'http://localhost:8000')
    const fetchSpy = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => WIRE_RESPONSE })
    vi.stubGlobal('fetch', fetchSpy)
    const { fetchPredictionHistory } = await import(
      '@/api/predictions/predictionHistory'
    )

    await fetchPredictionHistory(historyParamsFor('7d'))

    expect(fetchSpy).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/btc/price/history?range=30d&interval=1h&max_points=0',
      { headers: { Accept: 'application/json' } },
    )
  })

  it('throws rather than inventing candles when the service fails', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', 'http://localhost:8000')
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500 }))
    const { fetchPredictionHistory } = await import(
      '@/api/predictions/predictionHistory'
    )

    await expect(
      fetchPredictionHistory(historyParamsFor('24h')),
    ).rejects.toThrow(/500/)
  })

  it('falls back to simulated candles with no backend configured', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)
    const { fetchPredictionHistory } = await import(
      '@/api/predictions/predictionHistory'
    )

    const history = await fetchPredictionHistory(
      historyParamsFor('24h'),
      FIXED_NOW_MS,
    )

    expect(fetchSpy).not.toHaveBeenCalled()
    expect(history.source).toBe('simulated')
    expect(history.candles).toHaveLength(HISTORY_WINDOW['24h'].candles)
  })
})
