import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ALERTS_USER_ID } from '@/constants/alerts'
import type { MacroSubscription } from '@/types/alerts/macroAlert'

const GATEWAY_BASE = 'http://localhost:8000'
const SUBSCRIPTIONS_URL = `${GATEWAY_BASE}/api/v1/macro/subscriptions/${ALERTS_USER_ID}`
const SUBSCRIBE_URL = `${GATEWAY_BASE}/api/v1/macro/subscribe`

const LIVE_SUB: MacroSubscription = {
  id: 'live-sub',
  user_id: ALERTS_USER_ID,
  event_type: 'FED',
  subscribed: true,
  impact_filter: 'HIGH',
  timing: '12H',
  one_time: false,
  notify_in_app: true,
  notify_email: true,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

const axiosMock = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  delete: vi.fn(),
}))

vi.mock('axios', () => ({
  default: axiosMock,
}))

async function loadApi() {
  return import('@/api/alerts/macroAlerts')
}

describe('macroAlertApi', () => {
  beforeEach(() => {
    vi.resetModules()
    axiosMock.get.mockReset()
    axiosMock.post.mockReset()
    axiosMock.delete.mockReset()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.resetModules()
  })

  it('uses simulated subscriptions when no backend is configured', async () => {
    const { macroAlertApi } = await loadApi()
    const subscriptions = await macroAlertApi.getSubscriptions(ALERTS_USER_ID)

    expect(axiosMock.get).not.toHaveBeenCalled()
    expect(subscriptions.map((row) => row.event_type)).toEqual([
      'FED',
      'CPI',
      'GDP',
      'EMPLOYMENT',
    ])
  })

  it('lists only the subscriptions the gateway returns', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', GATEWAY_BASE)
    axiosMock.get.mockResolvedValue({
      data: {
        user_id: ALERTS_USER_ID,
        subscriptions: [
          {
            id: LIVE_SUB.id,
            user_id: ALERTS_USER_ID,
            event_type: 'fed',
            subscribed: true,
            impact_filter: 'high',
            timing: '12h',
            one_time: false,
            notify_in_app: true,
            notify_email: true,
            created_at: LIVE_SUB.created_at,
            updated_at: LIVE_SUB.updated_at,
          },
        ],
      },
    })
    const { macroAlertApi } = await loadApi()

    const subscriptions = await macroAlertApi.getSubscriptions(ALERTS_USER_ID)

    expect(axiosMock.get).toHaveBeenCalledWith(SUBSCRIPTIONS_URL, {
      headers: { Accept: 'application/json' },
    })
    expect(subscriptions).toHaveLength(1)
    expect(subscriptions[0]).toMatchObject({
      event_type: 'FED',
      subscribed: true,
      timing: '12H',
      one_time: false,
      notify_in_app: true,
      notify_email: true,
    })
  })

  it('subscribes through POST /macro/subscribe with lowercase API values', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', GATEWAY_BASE)
    axiosMock.post.mockResolvedValue({
      data: {
        id: 'created',
        user_id: ALERTS_USER_ID,
        event_type: 'cpi',
        subscribed: true,
        impact_filter: 'high',
      },
    })
    const { macroAlertApi } = await loadApi()

    const updated = await macroAlertApi.updateSubscription(ALERTS_USER_ID, {
      event_type: 'CPI',
      subscribed: true,
      timing: '1H',
      one_time: true,
      notify_in_app: false,
      notify_email: true,
    })

    expect(axiosMock.post).toHaveBeenCalledWith(
      SUBSCRIBE_URL,
      {
        user_id: ALERTS_USER_ID,
        event_type: 'cpi',
        subscribed: true,
        impact_filter: 'high',
        timing: '1h',
        one_time: true,
        notify_in_app: false,
        notify_email: true,
      },
      { headers: { Accept: 'application/json' } },
    )
    expect(updated.event_type).toBe('CPI')
    expect(updated.subscribed).toBe(true)
  })
})
