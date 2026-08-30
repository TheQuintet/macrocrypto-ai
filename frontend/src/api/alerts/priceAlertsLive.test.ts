import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ALERTS_USER_ID } from '@/constants/alerts'
import type { PriceAlert, PriceAlertListResponse } from '@/types/alerts/priceAlert'

const ALERT_API_BASE = 'http://localhost:8003'
const PRICE_ALERTS_URL = `${ALERT_API_BASE}/api/v1/alerts/price`

const LIVE_ALERT: PriceAlert = {
  id: 'live-alert-id',
  user_id: ALERTS_USER_ID,
  threshold_price: 72_000,
  alert_type: 'crosses_above',
  asset: 'BTC/USD',
  status: 'active',
  one_time: false,
  created_at: '2026-08-30T12:00:00.000Z',
  updated_at: '2026-08-30T12:00:00.000Z',
  triggered_at: null,
  notify_in_app: true,
  notify_email: true,
  name: 'Live breakout',
  description: null,
}

const LIVE_LIST: PriceAlertListResponse = {
  total: 1,
  limit: 50,
  offset: 0,
  alerts: [LIVE_ALERT],
}

const axiosMock = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
}))

vi.mock('axios', () => ({
  default: axiosMock,
}))

async function loadApi() {
  return import('@/api/alerts/priceAlerts')
}

describe('priceAlertApi with the alert service configured', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.stubEnv('VITE_ALERT_API_BASE_URL', ALERT_API_BASE)
    axiosMock.get.mockReset()
    axiosMock.post.mockReset()
    axiosMock.put.mockReset()
    axiosMock.delete.mockReset()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.resetModules()
  })

  it('lists alerts from the alert service', async () => {
    axiosMock.get.mockResolvedValue({ data: LIVE_LIST })
    const { priceAlertApi } = await loadApi()

    const response = await priceAlertApi.getAlerts(ALERTS_USER_ID, { status: 'active' })

    expect(axiosMock.get).toHaveBeenCalledWith(PRICE_ALERTS_URL, {
      params: { user_id: ALERTS_USER_ID, status: 'active' },
      headers: { Accept: 'application/json' },
    })
    expect(response).toEqual(LIVE_LIST)
  })

  it('creates an alert over axios', async () => {
    axiosMock.post.mockResolvedValue({ data: LIVE_ALERT })
    const { priceAlertApi } = await loadApi()
    const payload = {
      user_id: ALERTS_USER_ID,
      threshold_price: 72_000,
      alert_type: 'crosses_above' as const,
    }

    const created = await priceAlertApi.createAlert(payload)

    expect(axiosMock.post).toHaveBeenCalledWith(PRICE_ALERTS_URL, payload, {
      headers: { Accept: 'application/json' },
    })
    expect(created.id).toBe('live-alert-id')
  })

  it('throws instead of substituting seed alerts when the service fails', async () => {
    axiosMock.get.mockRejectedValue(new Error('offline'))
    const { priceAlertApi } = await loadApi()

    await expect(priceAlertApi.getAlerts(ALERTS_USER_ID)).rejects.toThrow('offline')
  })

  it('does not double up slashes on a trailing-slash base URL', async () => {
    vi.stubEnv('VITE_ALERT_API_BASE_URL', `${ALERT_API_BASE}/`)
    vi.resetModules()
    axiosMock.get.mockResolvedValue({ data: LIVE_LIST })
    const { priceAlertApi } = await loadApi()

    await priceAlertApi.getAlerts(ALERTS_USER_ID)

    expect(axiosMock.get).toHaveBeenCalledWith(PRICE_ALERTS_URL, expect.anything())
  })
})

describe('priceAlertApi with no alert service configured', () => {
  beforeEach(() => {
    vi.resetModules()
    axiosMock.get.mockReset()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.resetModules()
  })

  it('uses simulated data and does not call axios', async () => {
    const { priceAlertApi } = await loadApi()

    const response = await priceAlertApi.getAlerts(ALERTS_USER_ID)

    expect(axiosMock.get).not.toHaveBeenCalled()
    expect(response.alerts.length).toBeGreaterThan(0)
    expect(response.alerts[0]?.asset).toBe('BTC/USD')
  })

  it('stays simulated when only the data-service URL is set', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:8001')
    vi.resetModules()
    const { priceAlertApi } = await loadApi()

    const response = await priceAlertApi.getAlerts(ALERTS_USER_ID)

    expect(axiosMock.get).not.toHaveBeenCalled()
    expect(response.alerts.length).toBeGreaterThan(0)
  })
})
