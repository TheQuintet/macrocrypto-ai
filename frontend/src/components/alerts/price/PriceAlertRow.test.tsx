import { cleanup, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import { mockAlert } from './__tests__/testHelpers'
import {
  clickActivate,
  clickDeactivate,
  clickEdit,
  expectActivateControl,
  expectDeactivateControl,
  getDeleteButton,
  renderPriceAlertRow,
} from './PriceAlertRow.testHelpers'

describe('PriceAlertRow', () => {
  afterEach(() => {
    cleanup()
  })

  it('fills the shared columns: name, trigger, repeat, status', () => {
    renderPriceAlertRow()

    expect(screen.getByText('BTC Breakout Alert')).toBeInTheDocument()
    expect(screen.getByText('BTC/USD goes above $85,000.00')).toBeInTheDocument()
    expect(screen.getByText('One-time')).toBeInTheDocument()
    expect(screen.getByText('Active')).toBeInTheDocument()
    expectDeactivateControl()
  })

  it('falls back to the asset when no name is set', () => {
    renderPriceAlertRow({
      alert: { ...mockAlert, name: '', description: '' },
    })

    expect(screen.getByText('BTC/USD')).toBeInTheDocument()
    expect(screen.queryByText('BTC Breakout Alert')).not.toBeInTheDocument()
  })

  it('marks a repeating alert as recurring', () => {
    renderPriceAlertRow({ alert: { ...mockAlert, one_time: false } })

    expect(screen.getByText('Recurring')).toBeInTheDocument()
  })

  it('calls onDelete when delete is clicked', async () => {
    const user = userEvent.setup()
    const { onDelete, onEdit } = renderPriceAlertRow()

    await user.click(getDeleteButton())

    expect(onDelete).toHaveBeenCalledWith(mockAlert)
    expect(onEdit).not.toHaveBeenCalled()
  })

  it('opens edit from the alert name', async () => {
    const user = userEvent.setup()
    const { onEdit } = renderPriceAlertRow()

    await clickEdit(user)

    expect(onEdit).toHaveBeenCalledWith(mockAlert)
  })

  it('opens edit when any part of the row is clicked', async () => {
    const user = userEvent.setup()
    const { onEdit } = renderPriceAlertRow()

    await user.click(screen.getByText('BTC/USD goes above $85,000.00'))

    expect(onEdit).toHaveBeenCalledWith(mockAlert)
  })

  it('does not open edit when the status is toggled', async () => {
    const user = userEvent.setup()
    const { onEdit, onToggleStatus } = renderPriceAlertRow()

    await clickDeactivate(user)

    expect(onToggleStatus).toHaveBeenCalledWith(mockAlert)
    expect(onEdit).not.toHaveBeenCalled()
  })

  it('deactivates an active alert without opening edit', async () => {
    const user = userEvent.setup()
    const { onToggleStatus, onEdit } = renderPriceAlertRow()

    await clickDeactivate(user)

    expect(onToggleStatus).toHaveBeenCalledWith(mockAlert)
    expect(onEdit).not.toHaveBeenCalled()
  })

  it('activates an inactive alert from the row', async () => {
    const user = userEvent.setup()
    const inactiveAlert = { ...mockAlert, status: 'disabled' as const }
    const { onToggleStatus } = renderPriceAlertRow({ alert: inactiveAlert })

    expectActivateControl()
    await clickActivate(user)

    expect(onToggleStatus).toHaveBeenCalledWith(inactiveAlert)
  })
})
