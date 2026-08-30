import apiClient from '@/lib/apiClient'
import {
  simulateCreateAlert,
  simulateDeleteAlert,
  simulateGetAlert,
  simulateGetAlerts,
  simulateGetHistory,
  simulateTriggerAlert,
  simulateUpdateAlert,
} from './simulatedPriceAlerts'
import { withSimulatedFallback } from './withSimulatedFallback'
import type {
  PriceAlert,
  CreatePriceAlertRequest,
  UpdatePriceAlertRequest,
  PriceAlertHistory,
  PriceAlertListResponse,
} from '@/types/alerts/priceAlert'

export const priceAlertApi = {
  getAlerts: async (
    userId: string,
    params?: { status?: string; alert_type?: string; limit?: number; offset?: number },
  ): Promise<PriceAlertListResponse> =>
    withSimulatedFallback(
      async () => {
        const response = await apiClient.get('/alerts/price', {
          params: { user_id: userId, ...params },
        })
        return response.data
      },
      () => simulateGetAlerts(userId, params),
    ),

  getAlert: async (alertId: string): Promise<PriceAlert> =>
    withSimulatedFallback(
      async () => {
        const response = await apiClient.get(`/alerts/price/${alertId}`)
        return response.data
      },
      () => simulateGetAlert(alertId),
    ),

  createAlert: async (data: CreatePriceAlertRequest): Promise<PriceAlert> =>
    withSimulatedFallback(
      async () => {
        const response = await apiClient.post('/alerts/price', data)
        return response.data
      },
      () => simulateCreateAlert(data),
    ),

  updateAlert: async (
    alertId: string,
    data: UpdatePriceAlertRequest,
  ): Promise<PriceAlert> =>
    withSimulatedFallback(
      async () => {
        const response = await apiClient.put(`/alerts/price/${alertId}`, data)
        return response.data
      },
      () => simulateUpdateAlert(alertId, data),
    ),

  deleteAlert: async (alertId: string): Promise<void> =>
    withSimulatedFallback(
      () => apiClient.delete(`/alerts/price/${alertId}`).then(() => undefined),
      () => simulateDeleteAlert(alertId),
    ),

  triggerAlert: async (alertId: string): Promise<PriceAlert> =>
    withSimulatedFallback(
      async () => {
        const response = await apiClient.post(`/alerts/price/${alertId}/trigger`)
        return response.data
      },
      () => simulateTriggerAlert(alertId),
    ),

  getHistory: async (
    alertId: string,
    params?: { limit?: number; offset?: number },
  ): Promise<{ history: PriceAlertHistory[]; total: number }> =>
    withSimulatedFallback(
      async () => {
        const response = await apiClient.get(`/alerts/price/${alertId}/history`, {
          params,
        })
        return response.data
      },
      () => simulateGetHistory(alertId, params),
    ),
}
