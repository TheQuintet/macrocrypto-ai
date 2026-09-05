import axios from 'axios';
import type {
  CreatePredictionAlertRequest,
  PredictionAlert,
  PredictionAlertHistory,
  UpdatePredictionAlertRequest,
} from '@/types/alerts/predictionAlert';

const API_BASE = '/api/alerts/prediction';

// Flag to use mock data when backend is not ready
const USE_MOCK = true; // Set to false when backend is ready

// Mock data - with proper user_id matching your test user
const MOCK_USER_ID = 'b5e2102c-c4ac-46f9-95c3-2a3c389399a9';

let mockAlerts: PredictionAlert[] = [
  {
    id: '1',
    user_id: MOCK_USER_ID,
    threshold: 5,
    horizon: '24h',
    confidence_change: 5,
    status: 'active',
    one_time: false,
    name: 'Bullish Breakout Alert',
    description: 'Get notified when prediction shows strong upward movement',
    notify_in_app: true,
    notify_email: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: '2',
    user_id: MOCK_USER_ID,
    threshold: 10,
    horizon: '7d',
    confidence_change: 8,
    status: 'active',
    one_time: true,
    name: 'Major Trend Change',
    description: 'Alert for significant 7-day prediction changes',
    notify_in_app: true,
    notify_email: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: '3',
    user_id: MOCK_USER_ID,
    threshold: 2,
    horizon: '24h',
    confidence_change: 3,
    status: 'disabled',
    one_time: false,
    name: 'Minor Shifts',
    description: 'Get notified about small but frequent changes',
    notify_in_app: true,
    notify_email: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const mockHistory: PredictionAlertHistory[] = [
  {
    id: 'h1',
    alert_id: '1',
    previous_prediction: 68234.50,
    new_prediction: 70123.75,
    change_percentage: 2.77,
    horizon: '24h',
    threshold: 5,
    triggered_at: new Date(Date.now() - 3600000).toISOString(),
    recommendation: 'Bullish shift - consider increasing exposure',
    read: false,
  },
  {
    id: 'h2',
    alert_id: '2',
    previous_prediction: 71500.00,
    new_prediction: 68900.00,
    change_percentage: -3.64,
    horizon: '7d',
    threshold: 10,
    triggered_at: new Date(Date.now() - 7200000).toISOString(),
    recommendation: 'Bearish shift - consider adjusting position',
    read: true,
  },
];

// Helper to simulate API delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const predictionAlertApi = {
  // Get all alerts for a user
  getAlerts: async (userId: string): Promise<PredictionAlert[]> => {
    if (USE_MOCK) {
      await delay(500);
      console.log('📊 Mock: Getting prediction alerts for user:', userId);
      const filtered = mockAlerts.filter(a => a.user_id === userId);
      console.log('📊 Mock: Found', filtered.length, 'alerts');
      return filtered;
    }
    const response = await axios.get(`${API_BASE}?userId=${userId}`);
    return response.data;
  },

  // Create a new alert
  createAlert: async (data: CreatePredictionAlertRequest): Promise<PredictionAlert> => {
    if (USE_MOCK) {
      await delay(500);
      const newAlert: PredictionAlert = {
        id: String(mockAlerts.length + 1),
        ...data,
        status: 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      mockAlerts.push(newAlert);
      console.log('📊 Mock: Created prediction alert:', newAlert);
      return newAlert;
    }
    const response = await axios.post(API_BASE, data);
    return response.data;
  },

  // Update an existing alert
  updateAlert: async (
    alertId: string,
    data: UpdatePredictionAlertRequest,
  ): Promise<PredictionAlert> => {
    if (USE_MOCK) {
      await delay(500);
      const index = mockAlerts.findIndex(a => a.id === alertId);
      if (index === -1) throw new Error('Alert not found');
      mockAlerts[index] = { ...mockAlerts[index], ...data, updated_at: new Date().toISOString() };
      console.log('📊 Mock: Updated prediction alert:', mockAlerts[index]);
      return mockAlerts[index];
    }
    const response = await axios.patch(`${API_BASE}/${alertId}`, data);
    return response.data;
  },

  // Delete an alert
  deleteAlert: async (alertId: string): Promise<void> => {
    if (USE_MOCK) {
      await delay(500);
      mockAlerts = mockAlerts.filter(a => a.id !== alertId);
      console.log('📊 Mock: Deleted prediction alert:', alertId);
      return;
    }
    await axios.delete(`${API_BASE}/${alertId}`);
  },

  // Get alert history
  getHistory: async (
    userId: string,
    params?: {
      startDate?: string;
      endDate?: string;
      horizon?: '24h' | '7d';
      threshold?: 1 | 2 | 5 | 10;
      search?: string;
      page?: number;
      limit?: number;
    },
  ): Promise<{ history: PredictionAlertHistory[]; total: number; page: number; totalPages: number }> => {
    if (USE_MOCK) {
      await delay(500);
      let filtered = [...mockHistory];
      
      // Apply filters
      if (params?.horizon) {
        filtered = filtered.filter(h => h.horizon === params.horizon);
      }
      if (params?.threshold) {
        filtered = filtered.filter(h => h.threshold === params.threshold);
      }
      if (params?.search) {
        const search = params.search.toLowerCase();
        filtered = filtered.filter(h => 
          h.recommendation.toLowerCase().includes(search)
        );
      }
      if (params?.startDate) {
        filtered = filtered.filter(h => 
          new Date(h.triggered_at) >= new Date(params.startDate!)
        );
      }
      if (params?.endDate) {
        filtered = filtered.filter(h => 
          new Date(h.triggered_at) <= new Date(params.endDate!)
        );
      }

      const page = params?.page || 1;
      const limit = params?.limit || 10;
      const start = (page - 1) * limit;
      const paginated = filtered.slice(start, start + limit);

      return {
        history: paginated,
        total: filtered.length,
        page,
        totalPages: Math.ceil(filtered.length / limit),
      };
    }
    const response = await axios.get(`${API_BASE}/history`, {
      params: { userId, ...params },
    });
    return response.data;
  },

  // Export history
  exportHistory: async (userId: string, params?: {
    startDate?: string;
    endDate?: string;
    horizon?: '24h' | '7d';
  }): Promise<Blob> => {
    if (USE_MOCK) {
      await delay(500);
      let filtered = [...mockHistory];
      if (params?.horizon) {
        filtered = filtered.filter(h => h.horizon === params.horizon);
      }
      
      // Create CSV
      const headers = ['Previous Prediction,New Prediction,Change %,Horizon,Threshold,Recommendation,Triggered At\n'];
      const rows = filtered.map(h => 
        `${h.previous_prediction},${h.new_prediction},${h.change_percentage},${h.horizon},${h.threshold},${h.recommendation},${h.triggered_at}\n`
      );
      const csv = headers.concat(rows).join('');
      return new Blob([csv], { type: 'text/csv' });
    }
    const response = await axios.get(`${API_BASE}/history/export`, {
      params: { userId, ...params },
      responseType: 'blob',
    });
    return response.data;
  },

  // Get preview for an alert
  getPreview: async (
    data: CreatePredictionAlertRequest,
  ): Promise<PredictionAlert['preview']> => {
    if (USE_MOCK) {
      await delay(300);
      const baseChange = data.threshold + Math.random() * 3;
      const isBullish = Math.random() > 0.5;
      
      return {
        previousPrediction: 68234.50,
        newPrediction: isBullish ? 68234.50 + baseChange * 100 : 68234.50 - baseChange * 100,
        changePercentage: baseChange,
        confidence: 65 + Math.random() * 30,
        recommendation: isBullish 
          ? 'Bullish shift - consider increasing exposure'
          : 'Bearish shift - consider adjusting position',
        horizon: data.horizon,
      };
    }
    const response = await axios.post(`${API_BASE}/preview`, data);
    return response.data;
  },

  // Toggle alert status
  toggleStatus: async (alertId: string): Promise<PredictionAlert> => {
    if (USE_MOCK) {
      await delay(500);
      const index = mockAlerts.findIndex(a => a.id === alertId);
      if (index === -1) throw new Error('Alert not found');
      const newStatus = mockAlerts[index].status === 'active' ? 'disabled' : 'active';
      mockAlerts[index] = { ...mockAlerts[index], status: newStatus };
      console.log('📊 Mock: Toggled prediction alert:', mockAlerts[index]);
      return mockAlerts[index];
    }
    const response = await axios.patch(`${API_BASE}/${alertId}/toggle`);
    return response.data;
  },
};