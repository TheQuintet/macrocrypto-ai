import { generateMockMacroSubscriptions, generateMockMacroEvents } from './simulatedMacroAlerts';
import type { MacroSubscription, MacroEvent, MacroAlertHistory, EventType, EventTiming } from '@/types/alerts/macroAlert';

// Flag to use real API or simulated data
const USE_REAL_API = false;

export const macroAlertApi = {
  getSubscriptions: async (): Promise<MacroSubscription[]> => {
    if (USE_REAL_API) {
      console.warn('[MacroAlertApi] Real API not implemented yet');
    }
    return generateMockMacroSubscriptions();
  },

  updateSubscription: async (
    _userId: string,
    eventType: EventType,
    subscribed: boolean,
    oneTime: boolean = true
  ): Promise<MacroSubscription> => {
    if (USE_REAL_API) {
      console.warn('[MacroAlertApi] Real API not implemented yet');
    }
    return {
      id: crypto.randomUUID(),
      user_id: _userId,
      event_type: eventType,
      subscribed,
      impact_filter: null,
      timing: '1D' as EventTiming,
      one_time: oneTime,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
  },

  updateImpactFilter: async (): Promise<{ success: boolean }> => {
    if (USE_REAL_API) {
      console.warn('[MacroAlertApi] Real API not implemented yet');
    }
    return { success: true };
  },

  getUpcomingEvents: async (): Promise<MacroEvent[]> => {
    if (USE_REAL_API) {
      console.warn('[MacroAlertApi] Real API not implemented yet');
    }
    return generateMockMacroEvents();
  },

  getHistory: async (): Promise<MacroAlertHistory[]> => {
    if (USE_REAL_API) {
      console.warn('[MacroAlertApi] Real API not implemented yet');
    }
    return [];
  },
};

export default macroAlertApi;