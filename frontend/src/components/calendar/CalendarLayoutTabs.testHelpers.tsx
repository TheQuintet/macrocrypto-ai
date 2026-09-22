import { render, screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect, vi } from 'vitest'
import { CalendarLayoutTabs } from '@/components/calendar/CalendarLayoutTabs'

export function renderCalendarLayoutTabs() {
  const onChange = vi.fn()

  render(<CalendarLayoutTabs value="calendar" onChange={onChange} />)

  return { onChange }
}

export async function selectLayoutTab(user: UserEvent, name: string) {
  await user.click(screen.getByRole('tab', { name }))
}

export function expectLayoutTabSelected(name: string, selected: boolean) {
  expect(screen.getByRole('tab', { name })).toHaveAttribute(
    'aria-selected',
    String(selected),
  )
}
