import { render, screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect, vi } from 'vitest'
import { CalendarToolbar } from '@/components/calendar/CalendarToolbar'
import type {
  CalendarTimezoneMode,
  CalendarViewMode,
} from '@/types/economicCalendar'

export function renderCalendarToolbar(
  overrides: Partial<Parameters<typeof CalendarToolbar>[0]> = {},
) {
  const handlers = {
    onViewChange: vi.fn(),
    onTimezoneModeChange: vi.fn(),
    onPrevious: vi.fn(),
    onNext: vi.fn(),
    onToday: vi.fn(),
  }

  render(
    <CalendarToolbar
      label="March 2026"
      view="month"
      timezoneMode="local"
      timeZone="Europe/Bucharest"
      {...handlers}
      {...overrides}
    />,
  )

  return handlers
}

export async function clickPeriodButton(user: UserEvent, name: string) {
  await user.click(screen.getByRole('button', { name }))
}

export async function selectView(user: UserEvent, label: string) {
  await user.click(screen.getByRole('button', { name: label }))
}

export function getTimezoneSelect() {
  return screen.getByLabelText('Times in')
}

export async function selectTimezoneMode(
  user: UserEvent,
  mode: CalendarTimezoneMode,
) {
  await user.selectOptions(getTimezoneSelect(), mode)
}

export function expectViewSelected(label: string, selected: boolean) {
  expect(screen.getByRole('button', { name: label })).toHaveAttribute(
    'aria-pressed',
    String(selected),
  )
}

export function expectPeriodLabel(label: string) {
  expect(screen.getByRole('heading', { name: label })).toBeInTheDocument()
}

export function expectStepButtonsFor(view: CalendarViewMode) {
  expect(
    screen.getByRole('button', { name: `Previous ${view}` }),
  ).toBeInTheDocument()
  expect(
    screen.getByRole('button', { name: `Next ${view}` }),
  ).toBeInTheDocument()
}
