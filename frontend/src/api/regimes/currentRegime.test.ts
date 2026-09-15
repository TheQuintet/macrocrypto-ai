import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { CurrentRegimeResponse } from '@/types/regime'

/** A real `GET /api/v1/regimes/current` body, as the service serialises it. */
const WIRE_RESPONSE: CurrentRegimeResponse = {
  id: 7,
  regime_type: 'high_inflation',
  confidence: 81.5,
  visual_indicator: 'bear',
  identified_at: '2024-06-15T01:00:00.000Z',
  expires_at: '2024-06-16T01:00:00.000Z',
}

function response(body: unknown, init: { ok?: boolean; status?: number } = {}) {
  return vi.fn().mockResolvedValue({
    ok: init.ok ?? true,
    status: init.status ?? 200,
    json: async () => body,
  })
}

async function loadApi() {
  return import('@/api/regimes/currentRegime')
}

describe('fetchCurrentRegime without a backend', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.stubEnv('VITE_API_BASE_URL', '')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  it('returns simulated data, labelled as such, without any HTTP', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)
    const { fetchCurrentRegime } = await loadApi()

    const regime = await fetchCurrentRegime(Date.parse('2024-06-15T09:30:00Z'))

    expect(fetchSpy).not.toHaveBeenCalled()
    expect(regime?.source).toBe('simulated')
    expect(regime?.regimeType).toBe('rising_rates')
  })

  it('dates the simulated read from the service’s 01:00 UTC job', async () => {
    const { fetchCurrentRegime } = await loadApi()

    const regime = await fetchCurrentRegime(Date.parse('2024-06-15T09:30:00Z'))

    expect(regime?.identifiedAt).toBe('2024-06-15T01:00:00.000Z')
    expect(regime?.expiresAt).toBe('2024-06-16T01:00:00.000Z')
  })

  it('uses yesterday’s run before today’s has happened', async () => {
    const { fetchCurrentRegime } = await loadApi()

    const regime = await fetchCurrentRegime(Date.parse('2024-06-15T00:15:00Z'))

    expect(regime?.identifiedAt).toBe('2024-06-14T01:00:00.000Z')
  })
})

describe('fetchCurrentRegime with a backend configured', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:8001')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  it('calls the data service regime endpoint', async () => {
    const fetchSpy = response(WIRE_RESPONSE)
    vi.stubGlobal('fetch', fetchSpy)
    const { fetchCurrentRegime } = await loadApi()

    await fetchCurrentRegime()

    expect(fetchSpy).toHaveBeenCalledWith(
      'http://localhost:8001/api/v1/regimes/current',
      { headers: { Accept: 'application/json' } },
    )
  })

  it('maps the real payload and marks it live', async () => {
    vi.stubGlobal('fetch', response(WIRE_RESPONSE))
    const { fetchCurrentRegime } = await loadApi()

    const regime = await fetchCurrentRegime()

    expect(regime).toEqual({
      source: 'live',
      id: 7,
      regimeType: 'high_inflation',
      confidence: 81.5,
      visualIndicator: 'bear',
      identifiedAt: '2024-06-15T01:00:00.000Z',
      expiresAt: '2024-06-16T01:00:00.000Z',
    })
  })

  it('normalises a visual indicator the frontend does not know', async () => {
    vi.stubGlobal(
      'fetch',
      response({ ...WIRE_RESPONSE, visual_indicator: 'sideways' }),
    )
    const { fetchCurrentRegime } = await loadApi()

    expect((await fetchCurrentRegime())?.visualIndicator).toBe('neutral')
  })

  it('reads 404 as "not classified yet", not as a failure', async () => {
    vi.stubGlobal('fetch', response(null, { ok: false, status: 404 }))
    const { fetchCurrentRegime } = await loadApi()

    await expect(fetchCurrentRegime()).resolves.toBeNull()
  })

  it('throws on a server error rather than substituting simulated data', async () => {
    vi.stubGlobal('fetch', response(null, { ok: false, status: 500 }))
    const { fetchCurrentRegime } = await loadApi()

    await expect(fetchCurrentRegime()).rejects.toThrow(/500/)
  })
})
