import type {
  MacroSubscription,
  MacroEvent,
  EventType,
  EventImpact,
} from '@/types/alerts/macroAlert';

const EVENT_TYPES: EventType[] = ['FED', 'CPI', 'GDP', 'EMPLOYMENT'];
const IMPACTS: EventImpact[] = ['HIGH', 'MEDIUM', 'LOW'];

export const generateMockMacroSubscriptions = (): MacroSubscription[] => {
  return EVENT_TYPES.map((type) => ({
    id: crypto.randomUUID(),
    user_id: crypto.randomUUID(),
    event_type: type,
    subscribed: Math.random() > 0.5,
    impact_filter: Math.random() > 0.7 ? 'HIGH' : null,
    timing: ['1D', '12H', '1H'][Math.floor(Math.random() * 3)] as '1D' | '12H' | '1H',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }));
};

export const generateMockMacroEvents = (): MacroEvent[] => {
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

  return EVENT_TYPES.map((type) => {
    const days = Math.floor(Math.random() * 14) + 1;
    const date = new Date();
    date.setDate(date.getDate() + days);
    date.setHours(8 + Math.floor(Math.random() * 8), 0, 0, 0);

    return {
      id: crypto.randomUUID(),
      event_id: `event_${type}`,
      event_type: type,
      event_name: eventNames[type],
      description: descriptions[type],
      scheduled_at: date.toISOString(),
      timezone: 'UTC',
      impact: IMPACTS[Math.floor(Math.random() * IMPACTS.length)],
      subscribed: Math.random() > 0.5,
      notified: false,
    };
  });
};