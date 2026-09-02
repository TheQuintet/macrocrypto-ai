import { cleanup, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  LAST_RECEIVED_PRICE,
  clickOutsideDialog,
  getConditionSelect,
  expectValidationError,
  fillPrice,
  getCreateButton,
  getPriceInput,
  getSaveButton,
  expectAdvancedOpen,
  getRequiredSection,
  openAdvanced,
  pressEscape,
  renderCreateForm,
  renderEditForm,
  selectAlertCondition,
  submitCreateForm,
  toggleNamedSwitch,
} from '../PriceAlertForm.testHelpers'
import { mockAlert } from './testHelpers'
import { formatAlertPriceInput } from '../priceAlertRule'

vi.mock('@/hooks/useBtcPriceSnapshotQuery', () => ({
  useBtcPriceSnapshotQuery: vi.fn(),
}))

describe('PriceAlertForm', () => {
  afterEach(() => {
    cleanup()
  })

  it('proposes the last received BTC price', () => {
    renderCreateForm()

    expect(getPriceInput()).toHaveValue(formatAlertPriceInput(LAST_RECEIVED_PRICE))
  })

  it('leads with the price rule', () => {
    renderCreateForm()

    expect(screen.getByText('New price alert')).toBeInTheDocument()
    expect(getConditionSelect()).toHaveAccessibleName('BTC/USD condition')
    expect(getPriceInput()).toBeInTheDocument()
    expect(getCreateButton()).toBeInTheDocument()
    const required = within(getRequiredSection())
    expect(required.getByRole('switch', { name: 'One-time' })).toBeChecked()
    expect(
      required.getByText('You are notified for the next occurrence only.'),
    ).toBeInTheDocument()
  })

  it('folds the optional settings behind Advanced', async () => {
    const user = userEvent.setup()
    renderCreateForm()

    const required = within(getRequiredSection())
    expect(required.getByRole('textbox', { name: /^Price/ })).toBeInTheDocument()
    expect(required.getByRole('switch', { name: 'One-time' })).toBeInTheDocument()
    expect(screen.queryByRole('textbox', { name: 'Name' })).not.toBeInTheDocument()

    await openAdvanced(user)

    expect(screen.getByRole('textbox', { name: 'Name' })).toBeVisible()
    expect(screen.getByRole('textbox', { name: 'Note' })).toBeVisible()
    expect(screen.getByRole('switch', { name: 'In the app' })).toBeVisible()
    expect(screen.getByRole('switch', { name: 'Email' })).toBeVisible()
  })

  it('closes on Escape', async () => {
    const user = userEvent.setup()
    const { onOpenChange } = renderCreateForm()

    await pressEscape(user)

    expect(onOpenChange).toHaveBeenCalledWith(false)
  })

  it('closes when clicking outside the dialog', async () => {
    const user = userEvent.setup()
    const { onOpenChange } = renderCreateForm()

    await clickOutsideDialog(user)

    expect(onOpenChange).toHaveBeenCalledWith(false)
  })

  it('fills the edit form and shows the current status', () => {
    renderEditForm()

    expect(screen.getByText('Edit alert')).toBeInTheDocument()
    expect(screen.getByText('Active')).toBeInTheDocument()
    expect(screen.getByRole('switch', { name: 'Deactivate alert' })).toBeChecked()
    expect(getPriceInput()).toHaveValue('85,000.00')
    expect(getConditionSelect()).toHaveTextContent('Goes above')
    expect(getSaveButton()).toBeInTheDocument()
  })

  it('shows Inactive when editing a disabled alert', () => {
    renderEditForm({
      editingAlert: { ...mockAlert, status: 'disabled' },
    })

    expect(screen.getByText('Inactive')).toBeInTheDocument()
    expect(screen.queryByText('Active')).not.toBeInTheDocument()
    expect(screen.getByRole('switch', { name: 'Activate alert' })).not.toBeChecked()
  })

  it('updates the badge when the alert is paused', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    renderEditForm({ onSubmit })

    await toggleNamedSwitch(user, 'Deactivate alert')
    expect(screen.getByText('Inactive')).toBeInTheDocument()
    expect(screen.queryByText('Active')).not.toBeInTheDocument()

    await user.click(getSaveButton())
    await vi.waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ status: 'disabled' }))
    })
  })

  it('keeps the typed price when the condition changes', async () => {
    const user = userEvent.setup()
    renderCreateForm()

    await fillPrice(user, '85000')
    expect(getPriceInput()).toHaveValue('85,000.00')

    await selectAlertCondition(user, 'Goes below')

    expect(getConditionSelect()).toHaveTextContent('Goes below')
    expect(getPriceInput()).toHaveValue('85,000.00')
  })

  it('shows a validation error when the price is missing', async () => {
    const user = userEvent.setup()
    renderCreateForm({ lastPrice: null })

    await submitCreateForm(user)
    expectValidationError('Enter a price.')
  })

  it('requires at least one notification channel', async () => {
    const user = userEvent.setup()
    renderCreateForm()

    await fillPrice(user, '85000')
    await openAdvanced(user)
    await toggleNamedSwitch(user, 'In the app')
    await submitCreateForm(user)

    expectValidationError('Choose a notification.')
    expectAdvancedOpen()
  })

  it('submits the filled create form', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    renderCreateForm({ onSubmit })

    await fillPrice(user, '85000')
    await submitCreateForm(user)

    await vi.waitFor(() => {
      expect(onSubmit).toHaveBeenCalled()
    })
  })

  it('submits the proposed price when the user leaves it unchanged', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    renderCreateForm({ onSubmit })

    await submitCreateForm(user)

    await vi.waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ threshold_price: LAST_RECEIVED_PRICE }),
      )
    })
  })
})
