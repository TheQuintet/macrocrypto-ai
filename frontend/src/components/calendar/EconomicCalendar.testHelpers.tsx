import { screen, waitFor } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { expect } from 'vitest'
import { EconomicCalendar } from '@/components/calendar/EconomicCalendar'
import { renderWithQuery } from '@/test/renderWithQuery'

const FIND_TIMEOUT_MS = 5000

/**
 * With no API base URL configured (vitest pins them empty) the calendar runs
 * on its simulated feed, which is anchored to the current month.
 */
export function renderEconomicCalendar() {
  return renderWithQuery(
    <MemoryRouter>
      <EconomicCalendar userId="user-1" />
    </MemoryRouter>,
  )
}

/**
 * The grid and the mobile agenda both render — only CSS hides one — so an
 * event is expected to appear more than once.
 */
export function findEventChips(eventName: string) {
  return screen.findAllByRole(
    'button',
    { name: new RegExp(`^${eventName},`) },
    // The simulated feed resolves on a timer, and the first render in a file
    // carries the module-load cost — the default second is not always enough.
    { timeout: FIND_TIMEOUT_MS },
  )
}

export function queryEventChips(eventName: string) {
  return screen.queryAllByRole('button', {
    name: new RegExp(`^${eventName},`),
  })
}

export async function expectEventShown(eventName: string) {
  expect((await findEventChips(eventName)).length).toBeGreaterThan(0)
}

export async function expectEventGone(eventName: string) {
  await waitFor(
    () => {
      expect(queryEventChips(eventName)).toHaveLength(0)
    },
    { timeout: FIND_TIMEOUT_MS },
  )
}

export async function expectEventAnnounces(
  eventName: string,
  fragment: string,
) {
  const [chip] = await findEventChips(eventName)
  expect(chip.getAttribute('aria-label')).toContain(fragment)
}

export async function chooseEventType(user: UserEvent, value: string) {
  await user.selectOptions(
    screen.getByRole('combobox', { name: 'Event type filter' }),
    value,
  )
}

export async function chooseImpactLevel(user: UserEvent, value: string) {
  await user.selectOptions(
    screen.getByRole('combobox', { name: 'Impact level filter' }),
    value,
  )
}

export async function openEventDetails(user: UserEvent, eventName: string) {
  const [chip] = await findEventChips(eventName)
  await user.click(chip)
}

export async function switchToWeekView(user: UserEvent) {
  await user.click(screen.getByRole('button', { name: 'Week' }))
}

export async function stepToNextPeriod(user: UserEvent, view: string) {
  await user.click(screen.getByRole('button', { name: `Next ${view}` }))
}

export function expectSimulatedBadge() {
  expect(screen.getByText('Simulated')).toBeInTheDocument()
}

export function getPeriodHeading() {
  return screen.getByRole('heading', { level: 2 }).textContent
}

export async function switchToPastEvents(user: UserEvent) {
  await user.click(screen.getByRole('button', { name: 'Past events' }))
}

export function getPastEventsSection() {
  return screen.getByRole('region', { name: 'Past economic events' })
}
