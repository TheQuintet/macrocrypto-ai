import type {
  MacroSubscription,
  MacroEvent,
  EventType,
  EventImpact,
} from '@/types/alerts/macroAlert';

const EVENT_TYPES: EventType[] = ['FED', 'CPI', 'GDP', 'EMPLOYMENT'];

// Make subscriptions deterministic so they don't change on every refresh
let mockSubscriptions: MacroSubscription[] | null = null;
let mockEvents: MacroEvent[] | null = null;

export const generateMockMacroSubscriptions = (): MacroSubscription[] => {
  if (mockSubscriptions) return mockSubscriptions;

  mockSubscriptions = EVENT_TYPES.map((type) => {
    const isSubscribed = ['FED', 'CPI'].includes(type);
    const impact = type === 'FED' || type === 'CPI' ? 'HIGH' : 'MEDIUM';

    return {
      id: crypto.randomUUID(),
      user_id: 'test-user',
      event_type: type,
      subscribed: isSubscribed,
      impact_filter: impact as EventImpact,
      timing: '1D',
      one_time: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
  });

  return mockSubscriptions;
};

export const generateMockMacroEvents = (): MacroEvent[] => {
  if (mockEvents) return mockEvents;

  const eventNames: Record<EventType, string> = {
    FED: 'Federal Reserve Meeting',
    CPI: 'CPI Release',
    GDP: 'GDP Release',
    EMPLOYMENT: 'Employment Report',
  };

  const descriptions: Record<EventType, string> = {
    FED: 'FOMC interest rate decision',
    CPI: 'Consumer Price Index inflation data',
    GDP: 'Gross Domestic Product growth data',
    EMPLOYMENT: 'Non-farm payroll employment data',
  };

  mockEvents = EVENT_TYPES.map((type) => {
    const days = type === 'FED' ? 3 : type === 'CPI' ? 7 : type === 'GDP' ? 10 : 14;
    const date = new Date();
    date.setDate(date.getDate() + days);
    date.setHours(8 + Math.floor(Math.random() * 8), 0, 0, 0);

    const impact = type === 'FED' || type === 'CPI' ? 'HIGH' : 'MEDIUM';

    return {
      id: crypto.randomUUID(),
      event_id: `event_${type}`,
      event_type: type,
      event_name: eventNames[type],
      description: descriptions[type],
      scheduled_at: date.toISOString(),
      timezone: 'UTC',
      impact: impact as EventImpact,
      subscribed: ['FED', 'CPI'].includes(type),
      notified: false,
    };
  });

  return mockEvents;
};