import type { MacroEventSubscription } from '@/types/alerts/macroSubscription'

export const MACRO_SUBSCRIPTIONS_MOCK_LATENCY_MS = 140

/**
 * A plausible starting set for a frontend-only run: subscribed to the two
 * categories traders watch most, at different impact floors so the calendar
 * shows both a subscribed and an unsubscribed state.
 */
export async function simulateMacroSubscriptions(
  userId: string,
): Promise<MacroEventSubscription[]> {
  await new Promise((resolve) =>
    setTimeout(resolve, MACRO_SUBSCRIPTIONS_MOCK_LATENCY_MS),
  )

  const timestamp = '2026-01-01T00:00:00Z'

  return [
    {
      id: 'sim-subscription-fed',
      user_id: userId,
      event_type: 'fed',
      subscribed: true,
      impact_filter: 'medium',
      created_at: timestamp,
      updated_at: timestamp,
    },
    {
      id: 'sim-subscription-cpi',
      user_id: userId,
      event_type: 'cpi',
      subscribed: true,
      impact_filter: 'high',
      created_at: timestamp,
      updated_at: timestamp,
    },
  ]
}
