import axios from 'axios'
import { alertApiUrl } from '@/lib/apiConfig'
import {
  simulateCreateAlert,
  simulateDeleteAlert,
  simulateGetAlert,
  simulateGetAlerts,
  simulateGetHistory,
  simulateTriggerAlert,
  simulateUpdateAlert,
} from './simulatedPriceAlerts'
import type {
  PriceAlert,
  CreatePriceAlertRequest,
  UpdatePriceAlertRequest,
  PriceAlertHistory,
  PriceAlertListResponse,
} from '@/types/alerts/priceAlert'

/** Real endpoint on the alert service (see `app/api/routes.py`). */
export const PRICE_ALERTS_PATH = '/api/v1/alerts/price'

const JSON_HEADERS = { Accept: 'application/json' }

/**
 * Price-alert CRUD from the alert service.
 *
 * `VITE_ALERT_API_BASE_URL` is the switch (data-service prices use
 * `VITE_API_BASE_URL` on :8001). Unset → simulated seed data. Set → axios to
 * that host (alert-service on :8003) and a failed request throws rather than
 * quietly substituting seed rules.
 */
async function fromApiOrSimulate<T>(
  path: string,
  simulate: () => Promise<T>,
  live: (url: string) => Promise<T>,
): Promise<T> {
  const url = alertApiUrl(path)
  if (!url) {
    return simulate()
  }

  return live(url)
}

export const priceAlertApi = {
  getAlerts: async (
    userId: string,
    params?: { status?: string; alert_type?: string; limit?: number; offset?: number },
  ): Promise<PriceAlertListResponse> =>
    fromApiOrSimulate(
      PRICE_ALERTS_PATH,
      () => simulateGetAlerts(userId, params),
      async (url) => {
        const response = await axios.get<PriceAlertListResponse>(url, {
          params: { user_id: userId, ...params },
          headers: JSON_HEADERS,
        })
        return response.data
      },
    ),

  getAlert: async (alertId: string): Promise<PriceAlert> =>
    fromApiOrSimulate(
      `${PRICE_ALERTS_PATH}/${alertId}`,
      () => simulateGetAlert(alertId),
      async (url) => {
        const response = await axios.get<PriceAlert>(url, {
          headers: JSON_HEADERS,
        })
        return response.data
      },
    ),

  createAlert: async (data: CreatePriceAlertRequest): Promise<PriceAlert> =>
    fromApiOrSimulate(
      PRICE_ALERTS_PATH,
      () => simulateCreateAlert(data),
      async (url) => {
        const response = await axios.post<PriceAlert>(url, data, {
          headers: JSON_HEADERS,
        })
        return response.data
      },
    ),

  updateAlert: async (
    alertId: string,
    data: UpdatePriceAlertRequest,
  ): Promise<PriceAlert> =>
    fromApiOrSimulate(
      `${PRICE_ALERTS_PATH}/${alertId}`,
      () => simulateUpdateAlert(alertId, data),
      async (url) => {
        const response = await axios.put<PriceAlert>(url, data, {
          headers: JSON_HEADERS,
        })
        return response.data
      },
    ),

  deleteAlert: async (alertId: string): Promise<void> =>
    fromApiOrSimulate(
      `${PRICE_ALERTS_PATH}/${alertId}`,
      () => simulateDeleteAlert(alertId),
      (url) => axios.delete(url, { headers: JSON_HEADERS }).then(() => undefined),
    ),

  triggerAlert: async (alertId: string): Promise<PriceAlert> =>
    fromApiOrSimulate(
      `${PRICE_ALERTS_PATH}/${alertId}/trigger`,
      () => simulateTriggerAlert(alertId),
      async (url) => {
        const response = await axios.post<PriceAlert>(url, undefined, {
          headers: JSON_HEADERS,
        })
        return response.data
      },
    ),

  getHistory: async (
    alertId: string,
    params?: { limit?: number; offset?: number },
  ): Promise<{ history: PriceAlertHistory[]; total: number }> =>
    fromApiOrSimulate(
      `${PRICE_ALERTS_PATH}/${alertId}/history`,
      () => simulateGetHistory(alertId, params),
      async (url) => {
        const response = await axios.get<{
          history: PriceAlertHistory[]
          total: number
        }>(url, {
          params,
          headers: JSON_HEADERS,
        })
        return response.data
      },
    ),
}
