import { render, screen, within } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect } from 'vitest'
import { ChartIntervalSwitcher } from '@/components/dashboard/controls/ChartIntervalSwitcher'
import { usePreferencesStore } from '@/stores/preferencesStore'

export function renderChartIntervalSwitcher() {
  return render(<ChartIntervalSwitcher />)
}

export function getIntervalGroup() {
  return screen.getByRole('group', { name: 'Chart interval' })
}

export function getIntervalButton(label: string) {
  return within(getIntervalGroup()).getByRole('button', { name: label })
}

export async function selectChartInterval(user: UserEvent, label: string) {
  await user.click(getIntervalButton(label))
}

export function expectIntervalSelected(label: string) {
  expect(getIntervalButton(label)).toHaveAttribute('aria-pressed', 'true')
}

export function expectIntervalNotSelected(label: string) {
  expect(getIntervalButton(label)).toHaveAttribute('aria-pressed', 'false')
}

export function expectCandleInterval(value: '1d' | '1w') {
  expect(usePreferencesStore.getState().candleInterval).toBe(value)
}

export function expectIntervalDisabled(label: string) {
  expect(getIntervalButton(label)).toBeDisabled()
}
