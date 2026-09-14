import { fireEvent, render, screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect, vi } from 'vitest'
import { makeEconomicEvent } from '@/api/economicCalendar/economicCalendar.testHelpers'
import { EventHistory } from '@/components/calendar/EventHistory'
import type { EconomicEvent } from '@/types/economicCalendar'

/** Fixed dates well in the past, so "already happened" never depends on today. */
export const PAST_EVENTS: EconomicEvent[] = [
  makeEconomicEvent({
    event_name: 'CPI release',
    event_type: 'cpi',
    impact_level: 'high',
    event_date: '2024-03-12T13:30:00.000Z',
  }),
  makeEconomicEvent({
    event_name: 'Non-farm payrolls',
    event_type: 'employment',
    impact_level: 'medium',
    event_date: '2024-03-06T13:30:00.000Z',
  }),
  makeEconomicEvent({
    event_name: 'FOMC minutes',
    event_type: 'fed',
    impact_level: 'low',
    event_date: '2024-02-21T19:00:00.000Z',
  }),
]

/** Eleven past releases, enough to push the table onto a second page. */
export function manyPastEvents(): EconomicEvent[] {
  return Array.from({ length: 11 }, (_, index) =>
    makeEconomicEvent({
      event_name: `Past release ${index + 1}`,
      event_date: `2024-0${index < 9 ? '1' : '2'}-${String(
        (index % 28) + 1,
      ).padStart(2, '0')}T13:30:00.000Z`,
    }),
  )
}

export function renderEventHistory(events: EconomicEvent[] = PAST_EVENTS) {
  const onSelectEvent = vi.fn()

  render(
    <EventHistory
      events={events}
      timeZone="UTC"
      onSelectEvent={onSelectEvent}
    />,
  )

  return { onSelectEvent }
}

export function getEventButton(name: string) {
  return screen.getByRole('button', { name })
}

export function listedEventNames(): string[] {
  return screen
    .getAllByRole('row')
    .slice(1)
    .map((row) => row.querySelector('button')?.textContent ?? '')
}

export async function searchHistory(user: UserEvent, query: string) {
  await user.clear(screen.getByPlaceholderText('Search past events...'))
  if (query) {
    await user.type(screen.getByPlaceholderText('Search past events...'), query)
  }
}

/**
 * Date inputs are set directly rather than typed: `user.type` into a native
 * date field depends on the browser's segment order, which jsdom does not
 * model faithfully.
 */
export function setDateRange(start: string, end: string) {
  if (start) {
    fireEvent.change(screen.getByLabelText('From'), {
      target: { value: start },
    })
  }
  if (end) {
    fireEvent.change(screen.getByLabelText('To'), { target: { value: end } })
  }
}

export function expectEmptyMessage(text: string | RegExp) {
  expect(screen.getByText(text)).toBeInTheDocument()
}

export function expectCount(label: string) {
  expect(screen.getByText(label)).toBeInTheDocument()
}

export function queryPagination() {
  return screen.queryByRole('navigation')
}
