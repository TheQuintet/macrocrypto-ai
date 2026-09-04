import { render, screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect, vi } from 'vitest'
import { useBtcPriceSnapshotQuery } from '@/hooks/useBtcPriceSnapshotQuery'
import { PriceAlertForm } from './PriceAlertForm'
import { mockAlert } from './__tests__/testHelpers'
import type { CreatePriceAlertRequest, PriceAlert, UpdatePriceAlertRequest } from '@/types/alerts/priceAlert'
import type { BtcPriceSnapshot } from '@/types/btcPrice'

const defaultUserId = 'b5e2102c-c4ac-46f9-95c3-2a3c389399a9'

export const LAST_RECEIVED_PRICE = 64_213.5

const snapshotQuery = vi.mocked(useBtcPriceSnapshotQuery)

type FormProps = {
  open?: boolean
  onOpenChange?: (open: boolean) => void
  userId?: string
  editingAlert?: PriceAlert | null
  onSubmit?: (data: CreatePriceAlertRequest | UpdatePriceAlertRequest) => Promise<void>
  isLoading?: boolean
  lastPrice?: number | null
}

function snapshotFor(currentPrice: number | null | undefined): Partial<BtcPriceSnapshot> {
  return { currentPrice: currentPrice ?? null }
}

export function renderCreateForm(overrides: FormProps = {}) {
  const onSubmit = overrides.onSubmit ?? vi.fn().mockResolvedValue(undefined)
  const onOpenChange = overrides.onOpenChange ?? vi.fn()
  const lastPrice =
    overrides.lastPrice === undefined ? LAST_RECEIVED_PRICE : overrides.lastPrice

  snapshotQuery.mockReturnValue({
    data: snapshotFor(lastPrice),
  } as ReturnType<typeof useBtcPriceSnapshotQuery>)

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
  return screen.getByRole('textbox', { name: /^Price/ })
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
  await user.tab()
}

export function getConditionSelect() {
  return screen.getByRole('button', { name: /condition$/i })
}

export async function selectAlertCondition(user: UserEvent, label: string) {
  await user.click(getConditionSelect())
  await user.click(screen.getByRole('button', { name: label }))
}

export async function submitCreateForm(user: UserEvent) {
  await user.click(getCreateButton())
}

export async function pressEscape(user: UserEvent) {
  await user.keyboard('{Escape}')
}

export async function clickOutsideDialog(user: UserEvent) {
  await user.click(screen.getByTestId('dialog-overlay'))
}

export function getRequiredSection() {
  return screen.getByRole('region', { name: 'Required' })
}

export function getAdvancedToggle() {
  return screen.getByRole('button', { name: 'Advanced' })
}

export async function openAdvanced(user: UserEvent) {
  await user.click(getAdvancedToggle())
}

export function expectAdvancedOpen() {
  expect(getAdvancedToggle()).toHaveAttribute('aria-expanded', 'true')
}

export async function toggleNamedSwitch(user: UserEvent, name: string) {
  await user.click(screen.getByRole('switch', { name }))
}

export function expectValidationError(text: string) {
  expect(screen.getByText(text)).toBeInTheDocument()
}
