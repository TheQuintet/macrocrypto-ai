import { describe, expect, it } from 'vitest'
import {
  DEFAULT_PREDICTION_ASSET,
  toCreateApiPayload,
  toUiAlert,
  toUiThreshold,
  toUpdateApiPayload,
} from '@/lib/alerts/predictionAlertMapping'
import type { PredictionAlertApiRecord } from '@/types/alerts/predictionAlert'

const API_ROW: PredictionAlertApiRecord = {
  id: 'alert-1',
  user_id: 'user-1',
  threshold_percent: 5,
  horizon: '24h',
  direction: 'both',
  asset: 'BTC/USD',
  monitor_confidence: true,
  confidence_threshold_percent: 4,
  status: 'active',
  created_at: '2026-08-20T09:00:00.000Z',
  updated_at: '2026-08-28T11:20:00.000Z',
  triggered_at: null,
  notify_in_app: true,
  notify_email: false,
  name: 'Breakout',
  description: null,
}

describe('predictionAlertMapping', () => {
  it('snaps backend floats onto the UI threshold options', () => {
    expect(toUiThreshold(1)).toBe(1)
    expect(toUiThreshold(3.2)).toBe(2)
    expect(toUiThreshold(9)).toBe(10)
  })

  it('maps a create form into the alert-service body', () => {
    expect(
      toCreateApiPayload({
        user_id: 'user-1',
        threshold: 5,
        horizon: '24h',
        confidence_change: 4,
        one_time: true,
        notify_in_app: true,
        notify_email: false,
        name: 'Breakout',
      }),
    ).toEqual({
      user_id: 'user-1',
      threshold_percent: 5,
      horizon: '24h',
      direction: 'both',
      asset: DEFAULT_PREDICTION_ASSET,
      monitor_confidence: true,
      confidence_threshold_percent: 4,
      name: 'Breakout',
      description: null,
      notify_in_app: true,
      notify_email: false,
    })
  })

  it('omits one_time from update payloads and maps threshold_percent', () => {
    expect(
      toUpdateApiPayload({
        threshold: 10,
        one_time: true,
        status: 'disabled',
      }),
    ).toEqual({
      threshold_percent: 10,
      status: 'disabled',
    })
  })

  it('maps an API row onto the UI alert', () => {
    const alert = toUiAlert(API_ROW)
    expect(alert).toMatchObject({
      id: 'alert-1',
      threshold: 5,
      confidence_change: 4,
      direction: 'both',
      one_time: false,
      name: 'Breakout',
    })
  })

  it('drops a row that has no id or user', () => {
    expect(toUiAlert({ ...API_ROW, id: '' })).toBeNull()
    expect(toUiAlert({ ...API_ROW, user_id: '' })).toBeNull()
  })
})
