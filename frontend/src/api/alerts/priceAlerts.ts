import * as axios from 'axios';
import type {
  PriceAlert,
  CreatePriceAlertRequest,
  UpdatePriceAlertRequest,
  PriceAlertHistory,
  PriceAlertListResponse,
} from '@/types/alerts/priceAlert';

const API_BASE = '/api/v1';

export const priceAlertApi = {
  // Get all price alerts
  getAlerts: async (
    userId: string,
    params?: { status?: string; alert_type?: string; limit?: number; offset?: number }
  ): Promise<PriceAlertListResponse> => {
    const response = await axios.default.get(`${API_BASE}/alerts/price`, {
      params: { user_id: userId, ...params },
    });
    return response.data;
  },

  // Get a single price alert
  getAlert: async (alertId: string): Promise<PriceAlert> => {
    const response = await axios.default.get(`${API_BASE}/alerts/price/${alertId}`);
    return response.data;
  },

  // Create a price alert
  createAlert: async (data: CreatePriceAlertRequest): Promise<PriceAlert> => {
    const response = await axios.default.post(`${API_BASE}/alerts/price`, data);
    return response.data;
  },

  // Update a price alert
  updateAlert: async (alertId: string, data: UpdatePriceAlertRequest): Promise<PriceAlert> => {
    const response = await axios.default.put(`${API_BASE}/alerts/price/${alertId}`, data);
    return response.data;
  },

  // Delete a price alert
  deleteAlert: async (alertId: string): Promise<void> => {
    await axios.default.delete(`${API_BASE}/alerts/price/${alertId}`);
  },

  // Trigger an alert (for testing)
  triggerAlert: async (alertId: string): Promise<PriceAlert> => {
    const response = await axios.default.post(`${API_BASE}/alerts/price/${alertId}/trigger`);
    return response.data;
  },

  // Get alert history
  getHistory: async (
    alertId: string,
    params?: { limit?: number; offset?: number }
  ): Promise<{ history: PriceAlertHistory[]; total: number }> => {
    const response = await axios.default.get(`${API_BASE}/alerts/price/${alertId}/history`, { params });
    return response.data;
  },
};