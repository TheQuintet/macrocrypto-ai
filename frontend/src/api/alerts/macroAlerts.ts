import apiClient from '@/lib/apiClient';
import type { MacroSubscription, MacroEvent, MacroAlertHistory, EventType } from '@/types/alerts/macroAlert';
import { withSimulatedFallback } from './withSimulatedFallback';
import { generateMockMacroSubscriptions, generateMockMacroEvents } from './simulatedMacroAlerts';
import type { AxiosResponse, InternalAxiosRequestConfig } from 'axios';

// Helper to create a mock Axios response
const mockResponse = <T>(data: T): AxiosResponse<T> => ({
  data,
  status: 200,
  statusText: 'OK',
  headers: {},
  config: {} as InternalAxiosRequestConfig,
});

export const macroAlertApi = {
  getSubscriptions: async (userId: string): Promise<MacroSubscription[]> => {
    const live = () => apiClient.get('/macro/subscriptions', { params: { user_id: userId } });
    const simulate = async () => mockResponse(generateMockMacroSubscriptions());
    const response = await withSimulatedFallback(live, simulate);
    return response.data;
  },

  updateSubscription: async (
    userId: string,
    eventType: EventType,
    subscribed: boolean
  ): Promise<MacroSubscription> => {
    const live = () =>
      apiClient.put(`/macro/subscriptions/${eventType}`, {
        user_id: userId,
        subscribed,
      });
    const simulate = async () =>
      mockResponse({
        id: crypto.randomUUID(),
        user_id: userId,
        event_type: eventType,
        subscribed,
        impact_filter: null,
        timing: '1D' as const,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
    const response = await withSimulatedFallback(live, simulate);
    return response.data;
  },

  updateImpactFilter: async (
    userId: string,
    impactFilter: string | null
  ): Promise<{ success: boolean }> => {
    const live = () =>
      apiClient.put('/macro/subscriptions/filter', {
        user_id: userId,
        impact_filter: impactFilter,
      });
    const simulate = async () => mockResponse({ success: true });
    const response = await withSimulatedFallback(live, simulate);
    return response.data;
  },

  getUpcomingEvents: async (userId: string): Promise<MacroEvent[]> => {
    const live = () => apiClient.get('/macro/events/upcoming', { params: { user_id: userId } });
    const simulate = async () => mockResponse(generateMockMacroEvents());
    const response = await withSimulatedFallback(live, simulate);
    return response.data;
  },

  getHistory: async (userId: string): Promise<MacroAlertHistory[]> => {
    const live = () => apiClient.get('/macro/history', { params: { user_id: userId } });
    const simulate = async () => mockResponse([] as MacroAlertHistory[]);
    const response = await withSimulatedFallback(live, simulate);
    return response.data;
  },
};