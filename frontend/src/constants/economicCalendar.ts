import type {
  EconomicEventType,
  EventTypeFilter,
  ImpactLevelFilter,
} from '@/types/economicCalendar'

/** Categories data-service will return (`VALID_EVENT_TYPES`). */
export const ECONOMIC_EVENT_TYPES: EconomicEventType[] = [
  'fed',
  'cpi',
  'employment',
  'gdp',
]

export const EVENT_TYPE_LABELS: Record<EconomicEventType, string> = {
  fed: 'Fed',
  cpi: 'CPI',
  employment: 'Employment',
  gdp: 'GDP',
  other: 'Other',
}

export const EVENT_TYPE_FILTER_OPTIONS: {
  value: EventTypeFilter
  label: string
}[] = [
  { value: 'all', label: 'All types' },
  ...ECONOMIC_EVENT_TYPES.map((type) => ({
    value: type as EventTypeFilter,
    label: EVENT_TYPE_LABELS[type],
  })),
]

export const IMPACT_LEVEL_FILTER_OPTIONS: {
  value: ImpactLevelFilter
  label: string
}[] = [
  { value: 'all', label: 'All impact' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
]
