import { render, screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { expect, vi } from 'vitest'
import { makeEconomicEvent } from '@/api/economicCalendar/economicCalendar.testHelpers'
import { EventDetailsDialog } from '@/components/calendar/EventDetailsDialog'
import type { EconomicEvent } from '@/types/economicCalendar'

type RenderEventDetailsDialogOptions = {
  event?: EconomicEvent | null
  subscribed?: boolean | null
  timeZone?: string
}

export function renderEventDetailsDialog({
  event = makeEconomicEvent({
    event_name: 'FOMC rate decision',
    event_type: 'fed',
    impact_level: 'high',
    event_date: '2026-03-18T19:00:00.000Z',
    description: 'Federal Reserve policy decision.',
  }),
  subscribed = false,
  timeZone = 'UTC',
}: RenderEventDetailsDialogOptions = {}) {
  const onClose = vi.fn()

  render(
    <MemoryRouter>
      <EventDetailsDialog
        event={event}
        subscribed={subscribed}
        timeZone={timeZone}
        onClose={onClose}
      />
    </MemoryRouter>,
  )

  return { onClose }
}

export async function closeDialog(user: UserEvent) {
  await user.click(screen.getByRole('button', { name: 'Close' }))
}

export function expectDialogShows(text: string) {
  expect(screen.getByText(text)).toBeInTheDocument()
}

export function expectDialogMentions(fragment: string | RegExp) {
  expect(screen.getByText(fragment)).toBeInTheDocument()
}

export function expectManageAlertsLink() {
  expect(
    screen.getByRole('link', { name: 'Manage alerts' }),
  ).toHaveAttribute('href', '/alerts')
}

export function expectNothingRendered() {
  expect(screen.queryByRole('heading')).not.toBeInTheDocument()
}
