import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ALERTS_USER_ID } from '@/constants/alerts'
import type { PredictionAlertApiRecord } from '@/types/alerts/predictionAlert'
import { resetSimulatedPredictionAlerts } from '@/api/alerts/simulatedPredictionAlerts'

const GATEWAY_BASE = 'http://localhost:8000'
const PREDICTION_ALERTS_URL = `${GATEWAY_BASE}/api/v1/alerts/prediction/`

const LIVE_ROW: PredictionAlertApiRecord = {
  id: 'live-prediction-id',
  user_id: ALERTS_USER_ID,
  threshold_percent: 5,
  horizon: '24h',
  direction: 'both',
  asset: 'BTC/USD',
  monitor_confidence: true,
  confidence_threshold_percent: 5,
  status: 'active',
  created_at: '2026-08-30T12:00:00.000Z',
  updated_at: '2026-08-30T12:00:00.000Z',
  triggered_at: null,
  notify_in_app: true,
  notify_email: false,
  name: 'Live forecast',
  description: null,
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
  return import('@/api/alerts/predictionAlerts')
}

describe('predictionAlertApi with the API gateway configured', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', GATEWAY_BASE)
    axiosMock.get.mockReset()
    axiosMock.post.mockReset()
    axiosMock.put.mockReset()
    axiosMock.delete.mockReset()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.resetModules()
  })

  it('lists alerts from the API gateway and maps the wire shape', async () => {
    axiosMock.get.mockResolvedValue({
      data: { total: 1, limit: 50, offset: 0, alerts: [LIVE_ROW] },
    })
    const { predictionAlertApi } = await loadApi()

    const alerts = await predictionAlertApi.getAlerts(ALERTS_USER_ID)

    expect(axiosMock.get).toHaveBeenCalledWith(PREDICTION_ALERTS_URL, {
      params: { user_id: ALERTS_USER_ID },
      headers: { Accept: 'application/json' },
    })
    expect(alerts).toHaveLength(1)
    expect(alerts[0]?.id).toBe('live-prediction-id')
    expect(alerts[0]?.threshold).toBe(5)
  })

  it('creates an alert with threshold_percent, not the UI field names', async () => {
    axiosMock.post.mockResolvedValue({ data: LIVE_ROW })
    const { predictionAlertApi } = await loadApi()

    await predictionAlertApi.createAlert({
      user_id: ALERTS_USER_ID,
      threshold: 5,
      horizon: '24h',
      confidence_change: 5,
      one_time: true,
      notify_in_app: true,
      notify_email: false,
      name: 'Live forecast',
    })

    expect(axiosMock.post).toHaveBeenCalledWith(
      PREDICTION_ALERTS_URL,
      expect.objectContaining({
        user_id: ALERTS_USER_ID,
        threshold_percent: 5,
        confidence_threshold_percent: 5,
        direction: 'both',
      }),
      { headers: { Accept: 'application/json' } },
    )
  })

  it('updates with PUT instead of PATCH', async () => {
    axiosMock.put.mockResolvedValue({ data: LIVE_ROW })
    const { predictionAlertApi } = await loadApi()

    await predictionAlertApi.updateAlert('live-prediction-id', { status: 'disabled' })

    expect(axiosMock.put).toHaveBeenCalledWith(
      `${PREDICTION_ALERTS_URL}live-prediction-id`,
      { status: 'disabled' },
      { headers: { Accept: 'application/json' } },
    )
  })

  it('rejects a create response that cannot be mapped', async () => {
    axiosMock.post.mockResolvedValue({
      data: { ...LIVE_ROW, id: '', user_id: '' },
    })
    const { predictionAlertApi } = await loadApi()

    await expect(
      predictionAlertApi.createAlert({
        user_id: ALERTS_USER_ID,
        threshold: 5,
        horizon: '24h',
        confidence_change: 5,
        one_time: true,
        notify_in_app: true,
        notify_email: false,
      }),
    ).rejects.toThrow('Prediction alert response is missing id or user_id')
  })

  it('throws instead of substituting seed alerts when the service fails', async () => {
    axiosMock.get.mockRejectedValue(new Error('offline'))
    const { predictionAlertApi } = await loadApi()

    await expect(predictionAlertApi.getAlerts(ALERTS_USER_ID)).rejects.toThrow(
      'offline',
    )
  })
})

describe('predictionAlertApi with no API gateway configured', () => {
  beforeEach(() => {
    vi.resetModules()
    resetSimulatedPredictionAlerts()
    axiosMock.get.mockReset()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.resetModules()
  })

  it('uses simulated data and does not call axios', async () => {
    const { predictionAlertApi } = await loadApi()

    const alerts = await predictionAlertApi.getAlerts(ALERTS_USER_ID)

    expect(axiosMock.get).not.toHaveBeenCalled()
    expect(alerts.length).toBeGreaterThan(0)
    expect(alerts[0]?.asset).toBe('BTC/USD')
  })
})
