import type { EventTiming, EventType } from '@/types/alerts/macroAlert'

/** Display copy shared by the macro calendar table and the macro alert form. */
export const MACRO_EVENT_ICONS: Record<EventType, string> = {
  FED: '🏛️',
  CPI: '📊',
  GDP: '📈',
  EMPLOYMENT: '👔',
}

export const MACRO_EVENT_TITLES: Record<EventType, string> = {
  FED: 'Federal Reserve Meeting',
  CPI: 'CPI Release',
  GDP: 'GDP Release',
  EMPLOYMENT: 'Employment Report',
}

export const MACRO_TIMING_LABELS: Record<EventTiming, string> = {
  '1D': '1 day before',
  '12H': '12 hours before',
  '1H': '1 hour before',
}
