import { render, screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect, vi } from 'vitest'
import { AlertListItem } from './AlertListItem'
import { mockAlert } from './price/__tests__/testHelpers'
import type { PriceAlert } from '@/types/alerts/priceAlert'

type ListItemProps = {
  alert?: PriceAlert
  onDelete?: (alert: PriceAlert) => void
  onEdit?: (alert: PriceAlert) => void
  onToggleStatus?: (alert: PriceAlert) => void
}

export function renderAlertListItem(overrides: ListItemProps = {}) {
  const onDelete = overrides.onDelete ?? vi.fn()
  const onEdit = overrides.onEdit ?? vi.fn()
  const onToggleStatus = overrides.onToggleStatus ?? vi.fn()

  const view = render(
    <AlertListItem
      alert={overrides.alert ?? mockAlert}
      onDelete={onDelete}
      onEdit={onEdit}
      onToggleStatus={onToggleStatus}
    />,
  )

  return { ...view, onDelete, onEdit, onToggleStatus }
}

export function getEditRow() {
  return screen.getByRole('button', { name: 'Edit alert' })
}

export async function clickEditRow(user: UserEvent) {
  await user.click(getEditRow())
}

export function getDeleteButton() {
  return screen.getByRole('button', { name: 'Delete alert' })
}

export function getDeactivateButton() {
  return screen.getByRole('switch', { name: 'Deactivate alert' })
}

export function getActivateButton() {
  return screen.getByRole('switch', { name: 'Activate alert' })
}

export async function clickDeactivate(user: UserEvent) {
  await user.click(getDeactivateButton())
}

export async function clickActivate(user: UserEvent) {
  await user.click(getActivateButton())
}

export function expectDeactivateControl() {
  expect(getDeactivateButton()).toBeInTheDocument()
}

export function expectActivateControl() {
  expect(getActivateButton()).toBeInTheDocument()
}
