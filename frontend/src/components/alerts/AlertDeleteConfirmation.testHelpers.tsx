import { render, screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect, vi } from 'vitest'
import { AlertDeleteConfirmation } from './AlertDeleteConfirmation'
import { mockAlert } from './price/__tests__/testHelpers'
import type { PriceAlert } from '@/types/alerts/priceAlert'

type RenderArgs = {
  alert?: PriceAlert | null
  isLoading?: boolean
}

export function renderAlertDeleteConfirmation(overrides: RenderArgs = {}) {
  const onOpenChange = vi.fn()
  const onConfirm = vi.fn()

  const view = render(
    <AlertDeleteConfirmation
      alert={overrides.alert === undefined ? mockAlert : overrides.alert}
      onOpenChange={onOpenChange}
      onConfirm={onConfirm}
      isLoading={overrides.isLoading}
    />,
  )

  return { ...view, onOpenChange, onConfirm }
}

export function expectDeleteConfirmationClosed() {
  expect(screen.queryByRole('heading', { name: 'Delete alert' })).not.toBeInTheDocument()
}

export function expectDeleteDetail(label: string, value: string) {
  expect(screen.getByText(label)).toBeInTheDocument()
  expect(screen.getByText(value)).toBeInTheDocument()
}

export async function clickDeleteConfirm(user: UserEvent) {
  await user.click(screen.getByRole('button', { name: 'Delete' }))
}

export async function clickDeleteCancel(user: UserEvent) {
  await user.click(screen.getByRole('button', { name: 'Cancel' }))
}
