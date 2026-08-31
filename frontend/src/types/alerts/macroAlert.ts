// src/types/alerts/macroAlert.ts

export type EventType = 'FED' | 'CPI' | 'GDP' | 'EMPLOYMENT';
export type EventImpact = 'HIGH' | 'MEDIUM' | 'LOW';
export type EventTiming = '1D' | '12H' | '1H';

export interface MacroSubscription {
  id: string;
  user_id: string;
  event_type: EventType;
  subscribed: boolean;
  impact_filter: EventImpact | null;
  created_at: string;
  updated_at: string;
}

export interface MacroEvent {
  id: string;
  event_id: string;
  event_type: EventType;
  event_name: string;
  description: string;
  scheduled_at: string;
  timezone: string;
  impact: EventImpact;
  subscribed: boolean;
  notified: boolean;
}

export interface MacroAlertHistory {
  id: string;
  event_name: string;
  event_date: string;
  alert_timing: EventTiming;
  sent_date: string;
  event_type: EventType;
  impact: EventImpact;
}

export const EVENT_NAMES: Record<EventType, string> = {
  FED: 'Federal Reserve',
  CPI: 'Consumer Price Index',
  GDP: 'Gross Domestic Product',
  EMPLOYMENT: 'Employment Report',
};

export const EVENT_IMPACT_COLORS: Record<EventImpact, string> = {
  HIGH: 'text-red-500 border-red-500 bg-red-50 dark:bg-red-950/20',
  MEDIUM: 'text-yellow-500 border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20',
  LOW: 'text-green-500 border-green-500 bg-green-50 dark:bg-green-950/20',
};

export const EVENT_IMPACT_LABELS: Record<EventImpact, string> = {
  HIGH: 'High',
  MEDIUM: 'Medium',
  LOW: 'Low',
};
