import { render, screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect } from 'vitest'
import { TimeRangePicker } from '@/components/TimeRangePicker'
import { usePreferencesStore } from '@/stores/preferencesStore'

export function renderTimeRangePicker() {
  return render(<TimeRangePicker />)
}

export function getRangeButton(label: string) {
  return screen.getByRole('button', { name: label })
}

export async function selectTimeRange(user: UserEvent, range: string) {
  await user.click(getRangeButton(range))
}

export function expectRangeSelected(range: string) {
  expect(getRangeButton(range)).toHaveAttribute('aria-pressed', 'true')
  expect(usePreferencesStore.getState().timeRange).toBe(range)
}

export function expectRangeNotSelected(range: string) {
  expect(getRangeButton(range)).toHaveAttribute('aria-pressed', 'false')
}
