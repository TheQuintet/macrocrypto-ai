import apiClient from '@/lib/apiClient';
import type {
  PriceAlert,
  CreatePriceAlertRequest,
  UpdatePriceAlertRequest,
  PriceAlertHistory,
  PriceAlertListResponse,
} from '@/types/alerts/priceAlert';

export const priceAlertApi = {
  // Get all price alerts
  getAlerts: async (
    userId: string,
    params?: { status?: string; alert_type?: string; limit?: number; offset?: number }
  ): Promise<PriceAlertListResponse> => {
    const response = await apiClient.get('/alerts/price', {
      params: { user_id: userId, ...params },
    });
    return response.data;
  },

  // Get a single price alert
  getAlert: async (alertId: string): Promise<PriceAlert> => {
    const response = await apiClient.get(`/alerts/price/${alertId}`);
    return response.data;
  },

  // Create a price alert
  createAlert: async (data: CreatePriceAlertRequest): Promise<PriceAlert> => {
    const response = await apiClient.post('/alerts/price', data);
    return response.data;
  },

  // Update a price alert
  updateAlert: async (alertId: string, data: UpdatePriceAlertRequest): Promise<PriceAlert> => {
    const response = await apiClient.put(`/alerts/price/${alertId}`, data);
    return response.data;
  },

  // Delete a price alert
  deleteAlert: async (alertId: string): Promise<void> => {
    await apiClient.delete(`/alerts/price/${alertId}`);
  },

  // Trigger an alert (for testing)
  triggerAlert: async (alertId: string): Promise<PriceAlert> => {
    const response = await apiClient.post(`/alerts/price/${alertId}/trigger`);
    return response.data;
  },

  // Get alert history
  getHistory: async (
    alertId: string,
    params?: { limit?: number; offset?: number }
  ): Promise<{ history: PriceAlertHistory[]; total: number }> => {
    const response = await apiClient.get(`/alerts/price/${alertId}/history`, { params });
    return response.data;
  },
};
