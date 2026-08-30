import { render, screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect, vi } from 'vitest'
import type { AlertStatus } from '@/types/alerts/priceAlert'
import { AlertStatusToggle } from './AlertStatusToggle'

export function renderAlertStatusToggle(status: AlertStatus = 'active') {
  const onToggle = vi.fn()
  const view = render(<AlertStatusToggle status={status} onToggle={onToggle} />)
  return { ...view, onToggle }
}

export function getDeactivateSwitch() {
  return screen.getByRole('switch', { name: 'Deactivate alert' })
}

export function getActivateSwitch() {
  return screen.getByRole('switch', { name: 'Activate alert' })
}

export async function clickStatusSwitch(user: UserEvent, status: AlertStatus) {
  const control = status === 'active' || status === 'triggered'
    ? getDeactivateSwitch()
    : getActivateSwitch()
  await user.click(control)
}

export function expectDeactivateSwitch() {
  expect(getDeactivateSwitch()).toBeChecked()
}

export function expectActivateSwitch() {
  expect(getActivateSwitch()).not.toBeChecked()
}
