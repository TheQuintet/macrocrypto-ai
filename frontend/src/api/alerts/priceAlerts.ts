import axios from 'axios'
import { PRICE_ALERTS_PATH } from '@/constants/apiUrls'
import { apiUrl } from '@/lib/apiConfig'
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

const JSON_HEADERS = { Accept: 'application/json' }

/**
 * Price-alert CRUD from the alert service.
 *
 * `VITE_API_GATEWAY_BASE_URL` is the switch. Unset → simulated seed data.
 * Set → axios to the gateway and a failed request throws rather than
 * quietly substituting seed rules.
 */
async function fromApiOrSimulate<T>(
  path: string,
  simulate: () => Promise<T>,
  live: (url: string) => Promise<T>,
): Promise<T> {
  const url = apiUrl(path)
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
