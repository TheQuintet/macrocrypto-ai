import { create } from 'zustand';
import type { PriceAlert, CreatePriceAlertRequest, UpdatePriceAlertRequest } from '@/types/alerts/priceAlert';
import { priceAlertApi } from '@/api/alerts/priceAlerts';

interface PriceAlertState {
  alerts: PriceAlert[];
  isLoading: boolean;
  error: string | null;
  fetchAlerts: (userId: string, filters?: { status?: string; alert_type?: string }) => Promise<void>;
  createAlert: (data: CreatePriceAlertRequest) => Promise<PriceAlert>;
  updateAlert: (id: string, data: UpdatePriceAlertRequest) => Promise<PriceAlert>;
  deleteAlert: (id: string) => Promise<void>;
  triggerAlert: (id: string) => Promise<PriceAlert>;
  clearError: () => void;
}

// Custom error type for API errors
interface ApiError {
  message: string;
  response?: {
    data?: {
      detail?: string;
      message?: string;
    };
  };
}

// Helper to extract error message
const getErrorMessage = (error: unknown): string => {
  if (error && typeof error === 'object' && 'response' in error) {
    const apiError = error as ApiError;
    if (apiError.response?.data?.detail) {
      return apiError.response.data.detail;
    }
    if (apiError.response?.data?.message) {
      return apiError.response.data.message;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred';
};

export const usePriceAlertStore = create<PriceAlertState>((set) => ({
  alerts: [],
  isLoading: false,
  error: null,

  fetchAlerts: async (userId, filters) => {
    set({ isLoading: true, error: null });
    try {
      const response = await priceAlertApi.getAlerts(userId, filters);
      set({ alerts: response.alerts || [], isLoading: false });
    } catch (error) {
      set({ error: getErrorMessage(error), isLoading: false });
    }
  },

  createAlert: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const newAlert = await priceAlertApi.createAlert(data);
      set((state) => ({
        alerts: [newAlert, ...state.alerts],
        isLoading: false,
      }));
      return newAlert;
    } catch (error) {
      set({ error: getErrorMessage(error), isLoading: false });
      throw error;
    }
  },

  updateAlert: async (id, data) => {
    set({ isLoading: true, error: null });
    try {
      const updated = await priceAlertApi.updateAlert(id, data);
      set((state) => ({
        alerts: state.alerts.map((a) => (a.id === id ? updated : a)),
        isLoading: false,
      }));
      return updated;
    } catch (error) {
      set({ error: getErrorMessage(error), isLoading: false });
      throw error;
    }
  },

  deleteAlert: async (id) => {
    set({ isLoading: true, error: null });
    try {
      await priceAlertApi.deleteAlert(id);
      set((state) => ({
        alerts: state.alerts.filter((a) => a.id !== id),
        isLoading: false,
      }));
    } catch (error) {
      set({ error: getErrorMessage(error), isLoading: false });
      throw error;
    }
  },

  triggerAlert: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const triggered = await priceAlertApi.triggerAlert(id);
      set((state) => ({
        alerts: state.alerts.map((a) => (a.id === id ? triggered : a)),
        isLoading: false,
      }));
      return triggered;
    } catch (error) {
      set({ error: getErrorMessage(error), isLoading: false });
      throw error;
    }
  },

  clearError: () => set({ error: null }),
}));