import { cleanup, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  expectRuleSummary,
  expectValidationError,
  fillPrice,
  getCreateButton,
  getPriceInput,
  getSaveButton,
  renderCreateForm,
  renderEditForm,
  selectAlertCondition,
  submitCreateForm,
  toggleNamedSwitch,
} from '../PriceAlertForm.testHelpers'

describe('PriceAlertForm', () => {
  afterEach(() => {
    cleanup()
  })

  it('leads with the price rule and a live summary', () => {
    renderCreateForm()

    expect(screen.getByText('Create price alert')).toBeInTheDocument()
    expect(screen.getByText(/Set a BTC\/USD price rule and how you want to be notified/)).toBeInTheDocument()
    expect(screen.getByText('When should this fire?')).toBeInTheDocument()
    expect(screen.getByText('BTC/USD')).toBeInTheDocument()
    expect(getPriceInput()).toBeInTheDocument()
    expectRuleSummary('Enter a price to see when this alert will fire.')
    expect(getCreateButton()).toBeInTheDocument()
  })

  it('fills the edit form and shows the current status', () => {
    renderEditForm()

    expect(screen.getByText('Edit price alert')).toBeInTheDocument()
    expect(screen.getByText('Active')).toBeInTheDocument()
    expect(getPriceInput()).toHaveValue(85000)
    expectRuleSummary("We'll notify you when BTC/USD goes above $85,000.00.")
    expect(getSaveButton()).toBeInTheDocument()
  })

  it('updates the summary as the price and condition change', async () => {
    const user = userEvent.setup()
    renderCreateForm()

    await fillPrice(user, '85000')
    expectRuleSummary("We'll notify you when BTC/USD hits $85,000.00.")

    await selectAlertCondition(user, 'Goes below')
    expectRuleSummary("We'll notify you when BTC/USD goes below $85,000.00.")
  })

  it('shows a validation error when the price is missing', async () => {
    const user = userEvent.setup()
    renderCreateForm()

    await submitCreateForm(user)
    expectValidationError('Enter a price greater than 0.')
  })

  it('requires at least one notification channel', async () => {
    const user = userEvent.setup()
    renderCreateForm()

    await fillPrice(user, '85000')
    await toggleNamedSwitch(user, 'In the app')
    await submitCreateForm(user)

    expectValidationError('Choose at least one way to be notified.')
    expect(screen.getByText(/Sent to the email on your account/)).toBeInTheDocument()
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
})
