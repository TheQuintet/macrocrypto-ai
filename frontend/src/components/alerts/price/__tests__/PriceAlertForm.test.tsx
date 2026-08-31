import { cleanup, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  LAST_RECEIVED_PRICE,
  expectRuleSummary,
  expectValidationError,
  fillPrice,
  getCreateButton,
  getPriceInput,
  getSaveButton,
  openAdvancedTab,
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
    expectRuleSummary(`BTC/USD hits $64,213.50`)
  })

  it('leads with the price rule', () => {
    renderCreateForm()

    expect(screen.getByText('New alert')).toBeInTheDocument()
    expect(screen.getByText('BTC/USD')).toBeInTheDocument()
    expect(getPriceInput()).toBeInTheDocument()
    expect(getCreateButton()).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Alert' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.queryByLabelText('Name')).not.toBeInTheDocument()
    expect(screen.getByRole('switch', { name: 'One-time' })).toBeChecked()
    expect(screen.queryByRole('switch', { name: 'In the app' })).not.toBeInTheDocument()
  })

  it('keeps name, note, and notify on the Advanced tab', async () => {
    const user = userEvent.setup()
    renderCreateForm()

    await openAdvancedTab(user)

    expect(screen.getByRole('tab', { name: 'Advanced' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByLabelText('Name')).toBeInTheDocument()
    expect(screen.getByLabelText('Note')).toBeInTheDocument()
    expect(screen.getByRole('switch', { name: 'In the app' })).toBeInTheDocument()
    expect(screen.getByRole('switch', { name: 'Email' })).toBeInTheDocument()
    expect(screen.queryByLabelText(/^Price/)).not.toBeInTheDocument()
    expect(screen.queryByRole('switch', { name: 'One-time' })).not.toBeInTheDocument()
  })

  it('fills the edit form and shows the current status', () => {
    renderEditForm()

    expect(screen.getByText('Edit alert')).toBeInTheDocument()
    expect(screen.getByText('Active')).toBeInTheDocument()
    expect(screen.getByRole('switch', { name: 'Deactivate alert' })).toBeChecked()
    expect(getPriceInput()).toHaveValue('85,000.00')
    expectRuleSummary('BTC/USD goes above $85,000.00')
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

  it('updates the summary as the price and condition change', async () => {
    const user = userEvent.setup()
    renderCreateForm()

    await fillPrice(user, '85000')
    expect(getPriceInput()).toHaveValue('85,000.00')
    expectRuleSummary('BTC/USD hits $85,000.00')

    await selectAlertCondition(user, 'Goes below')
    expectRuleSummary('BTC/USD goes below $85,000.00')
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
    await openAdvancedTab(user)
    await toggleNamedSwitch(user, 'In the app')
    await submitCreateForm(user)

    expectValidationError('Choose a notification.')
    expect(screen.getByRole('switch', { name: 'Email' })).toBeInTheDocument()
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
