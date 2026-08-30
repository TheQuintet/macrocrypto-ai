import { render, screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect, vi } from 'vitest'
import { PriceAlertForm } from './PriceAlertForm'
import { mockAlert } from './__tests__/testHelpers'
import type { CreatePriceAlertRequest, PriceAlert, UpdatePriceAlertRequest } from '@/types/alerts/priceAlert'

const defaultUserId = 'b5e2102c-c4ac-46f9-95c3-2a3c389399a9'

type FormProps = {
  open?: boolean
  onOpenChange?: (open: boolean) => void
  userId?: string
  editingAlert?: PriceAlert | null
  onSubmit?: (data: CreatePriceAlertRequest | UpdatePriceAlertRequest) => Promise<void>
  isLoading?: boolean
}

export function renderCreateForm(overrides: FormProps = {}) {
  const onSubmit = overrides.onSubmit ?? vi.fn().mockResolvedValue(undefined)
  const onOpenChange = overrides.onOpenChange ?? vi.fn()

  const view = render(
    <PriceAlertForm
      open={overrides.open ?? true}
      onOpenChange={onOpenChange}
      userId={overrides.userId ?? defaultUserId}
      editingAlert={overrides.editingAlert ?? null}
      onSubmit={onSubmit}
      isLoading={overrides.isLoading ?? false}
    />,
  )

  return { ...view, onSubmit, onOpenChange }
}

export function renderEditForm(overrides: FormProps = {}) {
  return renderCreateForm({
    editingAlert: mockAlert,
    ...overrides,
  })
}

export function getPriceInput() {
  return screen.getByRole('spinbutton', { name: /^Price/ })
}

export function getCreateButton() {
  return screen.getByRole('button', { name: 'Create alert' })
}

export function getSaveButton() {
  return screen.getByRole('button', { name: 'Save changes' })
}

export async function fillPrice(user: UserEvent, value: string) {
  const input = getPriceInput()
  await user.clear(input)
  await user.type(input, value)
}

export async function selectAlertCondition(user: UserEvent, label: string) {
  await user.click(screen.getByRole('button', { name: 'Condition' }))
  await user.click(screen.getByRole('button', { name: label }))
}

export async function submitCreateForm(user: UserEvent) {
  await user.click(getCreateButton())
}

export async function toggleNamedSwitch(user: UserEvent, name: string) {
  await user.click(screen.getByRole('switch', { name }))
}

export function expectRuleSummary(text: string) {
  expect(screen.getByRole('status')).toHaveTextContent(text)
}

export function expectValidationError(text: string) {
  expect(screen.getByText(text)).toBeInTheDocument()
}
