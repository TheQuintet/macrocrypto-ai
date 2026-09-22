import type {
  MacroSubscription,
  EventType,
  EventImpact,
} from '@/types/alerts/macroAlert';

const EVENT_TYPES: EventType[] = ['FED', 'CPI', 'GDP', 'EMPLOYMENT'];

// Make subscriptions deterministic so they don't change on every refresh
let mockSubscriptions: MacroSubscription[] | null = null;

export const generateMockMacroSubscriptions = (
  userId = 'test-user',
): MacroSubscription[] => {
  if (mockSubscriptions) return mockSubscriptions;

  mockSubscriptions = EVENT_TYPES.map((type) => {
    const isSubscribed = ['FED', 'CPI'].includes(type);
    const impact = type === 'FED' || type === 'CPI' ? 'HIGH' : 'MEDIUM';

    return {
      id: crypto.randomUUID(),
      user_id: userId,
      event_type: type,
      subscribed: isSubscribed,
      impact_filter: impact as EventImpact,
      // Mirrors the live payload: the alert service sends neither field.
      timing: null,
      one_time: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
  });

  return mockSubscriptions;
};