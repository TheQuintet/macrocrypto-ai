import { render, screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect, vi } from 'vitest'
import { AlertStatusFilter } from './AlertStatusFilter'
import type { AlertListStatusFilter } from './shared/alertStatus'

const defaultCounts = { all: 3, active: 2, inactive: 1 }

export function renderAlertStatusFilter(value: AlertListStatusFilter = 'all') {
  const onChange = vi.fn()
  const view = render(
    <AlertStatusFilter value={value} onChange={onChange} counts={defaultCounts} />,
  )
  return { ...view, onChange }
}

/** Buttons read "All (3)", so match on the label and let the count vary. */
export function getFilterButton(label: string) {
  return screen.getByRole('button', { name: new RegExp(`^${label} \\(\\d+\\)$`) })
}

export async function selectAlertStatusFilter(user: UserEvent, label: string) {
  await user.click(getFilterButton(label))
}

export function expectAlertStatusFilterSelected(label: string) {
  expect(getFilterButton(label)).toHaveAttribute('aria-pressed', 'true')
}
