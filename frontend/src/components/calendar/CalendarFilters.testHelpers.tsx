import { render, screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect, vi } from 'vitest'
import { CalendarFilters } from '@/components/calendar/CalendarFilters'
import type {
  EventTypeFilter,
  ImpactLevelFilter,
} from '@/types/economicCalendar'

export function renderCalendarFilters(
  eventType: EventTypeFilter = 'all',
  impactLevel: ImpactLevelFilter = 'all',
) {
  const handlers = {
    onEventTypeChange: vi.fn(),
    onImpactLevelChange: vi.fn(),
  }

  render(
    <CalendarFilters
      eventType={eventType}
      impactLevel={impactLevel}
      {...handlers}
    />,
  )

  return handlers
}

export function getEventTypeFilter() {
  return screen.getByRole('combobox', { name: 'Event type filter' })
}

export function getImpactLevelFilter() {
  return screen.getByRole('combobox', { name: 'Impact level filter' })
}

export async function selectEventType(
  user: UserEvent,
  value: EventTypeFilter,
) {
  await user.selectOptions(getEventTypeFilter(), value)
}

export async function selectImpactLevel(
  user: UserEvent,
  value: ImpactLevelFilter,
) {
  await user.selectOptions(getImpactLevelFilter(), value)
}

export function expectFilterValues(
  eventType: EventTypeFilter,
  impactLevel: ImpactLevelFilter,
) {
  expect(getEventTypeFilter()).toHaveValue(eventType)
  expect(getImpactLevelFilter()).toHaveValue(impactLevel)
}
