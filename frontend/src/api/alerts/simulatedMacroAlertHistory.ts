import type {
  MacroAlertHistoryEntry,
  MacroAlertHistoryResponse,
  MacroAlertTiming,
} from '@/types/alerts/macroAlertHistory';
import type {
  EconomicEventType,
  EventImpactLevel,
} from '@/types/economicCalendar';

export const MACRO_ALERT_HISTORY_MOCK_LATENCY_MS = 160;

const DAY_MS = 24 * 60 * 60 * 1000;
const HOUR_MS = 60 * 60 * 1000;

type SeedAlert = {
  event_name: string;
  event_type: EconomicEventType;
  impact: EventImpactLevel;
  timing: MacroAlertTiming;
  description: string;
  /** How many days before "now" the event took place. */
  daysAgo: number;
};

/** Roughly the last two months of releases a subscribed trader would have been warned about. */
const SEED_ALERTS: SeedAlert[] = [
  {
    event_name: 'FOMC rate decision',
    event_type: 'fed',
    impact: 'high',
    timing: '12h',
    description: 'Federal Reserve policy decision and statement.',
    daysAgo: 3,
  },
  {
    event_name: 'CPI release',
    event_type: 'cpi',
    impact: 'high',
    timing: '1d',
    description: 'Monthly consumer price index.',
    daysAgo: 9,
  },
  {
    event_name: 'Non-farm payrolls',
    event_type: 'employment',
    impact: 'high',
    timing: '1d',
    description: 'Headline US jobs report.',
    daysAgo: 15,
  },
  {
    event_name: 'GDP (second estimate)',
    event_type: 'gdp',
    impact: 'medium',
    timing: '1h',
    description: 'Revision to quarterly growth.',
    daysAgo: 22,
  },
  {
    event_name: 'FOMC minutes',
    event_type: 'fed',
    impact: 'medium',
    timing: '12h',
    description: 'Minutes of the previous policy meeting.',
    daysAgo: 28,
  },
  {
    event_name: 'CPI release',
    event_type: 'cpi',
    impact: 'high',
    timing: '1d',
    description: 'Monthly consumer price index.',
    daysAgo: 40,
  },
  {
    event_name: 'Non-farm payrolls',
    event_type: 'employment',
    impact: 'high',
    timing: '12h',
    description: 'Headline US jobs report.',
    daysAgo: 46,
  },
  {
    event_name: 'FOMC rate decision',
    event_type: 'fed',
    impact: 'high',
    timing: '1d',
    description: 'Federal Reserve policy decision and statement.',
    daysAgo: 52,
  },
  {
    event_name: 'Initial jobless claims',
    event_type: 'employment',
    impact: 'low',
    timing: '1h',
    description: 'Weekly claims.',
    daysAgo: 59,
  },
  {
    event_name: 'GDP (advance estimate)',
    event_type: 'gdp',
    impact: 'medium',
    timing: '1d',
    description: 'First read on quarterly growth.',
    daysAgo: 66,
  },
  {
    event_name: 'CPI release',
    event_type: 'cpi',
    impact: 'high',
    timing: '12h',
    description: 'Monthly consumer price index.',
    daysAgo: 71,
  },
  {
    event_name: 'FOMC minutes',
    event_type: 'fed',
    impact: 'medium',
    timing: '1d',
    description: 'Minutes of the previous policy meeting.',
    daysAgo: 80,
  },
];

const TIMING_LEAD_MS: Record<MacroAlertTiming, number> = {
  '1d': DAY_MS,
  '12h': 12 * HOUR_MS,
  '1h': HOUR_MS,
};

/**
 * Stand-in history for a frontend-only run, anchored to the current date so
 * the date-range filter always has something to bite on.
 */
export async function simulateMacroAlertHistory(
  userId: string,
  now: Date = new Date(),
): Promise<MacroAlertHistoryResponse> {
  await new Promise((resolve) =>
    setTimeout(resolve, MACRO_ALERT_HISTORY_MOCK_LATENCY_MS),
  );

  const notifications: MacroAlertHistoryEntry[] = SEED_ALERTS.map(
    (seed, index) => {
      const eventDate = new Date(now.getTime() - seed.daysAgo * DAY_MS);
      const sentAt = new Date(
        eventDate.getTime() - TIMING_LEAD_MS[seed.timing],
      );

      return {
        id: `sim-macro-notification-${index + 1}`,
        user_id: userId,
        alert_id: `sim-macro-alert-${seed.event_type}`,
        event_name: seed.event_name,
        event_type: seed.event_type,
        event_date: eventDate.toISOString(),
        timing: seed.timing,
        impact: seed.impact,
        description: seed.description,
        read: index > 1,
        sent_at: sentAt.toISOString(),
      };
    },
  );

  return {
    total: notifications.length,
    limit: notifications.length,
    offset: 0,
    notifications,
  };
}
