import type { MacroEventSubscription } from '@/types/alerts/macroSubscription'

/** An active Fed subscription at the `high` impact floor by default. */
export function makeMacroSubscription(
  overrides: Partial<MacroEventSubscription> = {},
): MacroEventSubscription {
  return {
    id: 'subscription-1',
    user_id: 'user-1',
    event_type: 'fed',
    subscribed: true,
    impact_filter: 'high',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}
