import { render, screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect, vi } from 'vitest'
import { AlertStatusFilter } from './AlertStatusFilter'
import type { AlertListStatusFilter } from './shared/alertStatus'

export function renderAlertStatusFilter(value: AlertListStatusFilter = 'all') {
  const onChange = vi.fn()
  const view = render(<AlertStatusFilter value={value} onChange={onChange} />)
  return { ...view, onChange }
}

export function getFilterButton(label: string) {
  return screen.getByRole('button', { name: label })
}

export async function selectAlertStatusFilter(user: UserEvent, label: string) {
  await user.click(getFilterButton(label))
}

export function expectAlertStatusFilterSelected(label: string) {
  expect(getFilterButton(label)).toHaveAttribute('aria-pressed', 'true')
}
