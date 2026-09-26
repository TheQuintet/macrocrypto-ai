import type {
  MacroSubscription,
  EventType,
  EventImpact,
  MacroSubscriptionWrite,
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
      timing: '1D',
      one_time: true,
      notify_in_app: true,
      notify_email: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
  });

  return mockSubscriptions;
};

export function upsertMockMacroSubscription(
  userId: string,
  write: MacroSubscriptionWrite,
): MacroSubscription {
  generateMockMacroSubscriptions(userId)
  if (!mockSubscriptions) {
    mockSubscriptions = []
  }

  const now = new Date().toISOString()
  const existing = mockSubscriptions.find(
    (row) => row.event_type === write.event_type,
  )

  if (existing) {
    existing.subscribed = write.subscribed
    existing.timing = write.timing
    existing.one_time = write.one_time
    existing.notify_in_app = write.notify_in_app
    existing.notify_email = write.notify_email
    existing.updated_at = now
    return existing
  }

  const created: MacroSubscription = {
    id: crypto.randomUUID(),
    user_id: userId,
    event_type: write.event_type,
    subscribed: write.subscribed,
    impact_filter: 'HIGH',
    timing: write.timing,
    one_time: write.one_time,
    notify_in_app: write.notify_in_app,
    notify_email: write.notify_email,
    created_at: now,
    updated_at: now,
  }

  mockSubscriptions.push(created)
  return created
}

export async function removeMockMacroSubscription(
  eventType: EventType,
): Promise<void> {
  generateMockMacroSubscriptions()
  if (!mockSubscriptions) return

  mockSubscriptions = mockSubscriptions.filter(
    (row) => row.event_type !== eventType,
  )
}