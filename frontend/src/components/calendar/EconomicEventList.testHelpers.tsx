import { render, screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect, vi } from 'vitest'
import { makeEconomicEvent } from '@/api/economicCalendar/economicCalendar.testHelpers'
import { EconomicEventList } from '@/components/calendar/EconomicEventList'
import type { EconomicEvent } from '@/types/economicCalendar'

export const LIST_EVENTS = [
  makeEconomicEvent({
    id: 1,
    event_name: 'CPI release',
    event_type: 'cpi',
    event_date: '2026-03-12T13:30:00.000Z',
    impact_level: 'high',
  }),
  makeEconomicEvent({
    id: 2,
    event_name: 'FOMC rate decision',
    event_type: 'fed',
    event_date: '2026-03-18T19:00:00.000Z',
    impact_level: 'high',
  }),
]

export function renderEconomicEventList(
  overrides: {
    events?: EconomicEvent[]
    periodLabel?: string
    isSubscribed?: (event: EconomicEvent) => boolean | null
  } = {},
) {
  const onSelectEvent = vi.fn()

  render(
    <EconomicEventList
      events={overrides.events ?? LIST_EVENTS}
      periodLabel={overrides.periodLabel ?? 'March 2026'}
      timeZone="UTC"
      isSubscribed={overrides.isSubscribed ?? (() => false)}
      onSelectEvent={onSelectEvent}
    />,
  )

  return { onSelectEvent }
}

export function listedEventNames() {
  return screen.getAllByRole('button').map((button) => button.textContent)
}

export async function openListedEvent(user: UserEvent, eventName: string) {
  await user.click(screen.getByRole('button', { name: eventName }))
}

export function expectEmptyPeriod(periodLabel: string) {
  expect(screen.getByText(`No events in ${periodLabel}.`)).toBeInTheDocument()
}
