import { cleanup, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import { mockAlert } from '../price/__tests__/testHelpers'
import {
  clickActivate,
  clickDeactivate,
  clickEditRow,
  expectActivateControl,
  expectDeactivateControl,
  getDeleteButton,
  renderAlertListItem,
} from '../AlertListItem.testHelpers'

describe('AlertListItem', () => {
  afterEach(() => {
    cleanup()
  })

  it('renders the set name as the row title', () => {
    renderAlertListItem()

    expect(screen.getByText('BTC Breakout Alert')).toBeInTheDocument()
    expect(screen.getByText('BTC/USD goes above $85,000.00')).toBeInTheDocument()
    expect(screen.getByText('Active')).toBeInTheDocument()
    expectDeactivateControl()
  })

  it('uses the price rule as the title when no name is set', () => {
    renderAlertListItem({
      alert: { ...mockAlert, name: '', description: '' },
    })

    expect(screen.getByText('BTC/USD goes above $85,000.00')).toBeInTheDocument()
    expect(screen.queryByText('BTC Breakout Alert')).not.toBeInTheDocument()
  })

  it('calls onDelete when delete is clicked', async () => {
    const user = userEvent.setup()
    const { onDelete } = renderAlertListItem()

    await user.click(getDeleteButton())

    expect(onDelete).toHaveBeenCalledTimes(1)
    expect(onDelete).toHaveBeenCalledWith(mockAlert)
  })

  it('opens edit when the row is clicked', async () => {
    const user = userEvent.setup()
    const { onEdit } = renderAlertListItem()

    await clickEditRow(user)

    expect(onEdit).toHaveBeenCalledTimes(1)
    expect(onEdit).toHaveBeenCalledWith(mockAlert)
  })

  it('does not open edit when delete is clicked', async () => {
    const user = userEvent.setup()
    const { onEdit, onDelete } = renderAlertListItem()

    await user.click(getDeleteButton())

    expect(onDelete).toHaveBeenCalledTimes(1)
    expect(onEdit).not.toHaveBeenCalled()
  })

  it('does not open edit when the alert is paused from the row', async () => {
    const user = userEvent.setup()
    const { onEdit, onToggleStatus } = renderAlertListItem()

    await clickDeactivate(user)

    expect(onToggleStatus).toHaveBeenCalledTimes(1)
    expect(onEdit).not.toHaveBeenCalled()
  })

  it('deactivates an active alert from the row action', async () => {
    const user = userEvent.setup()
    const { onToggleStatus } = renderAlertListItem()

    await clickDeactivate(user)

    expect(onToggleStatus).toHaveBeenCalledTimes(1)
    expect(onToggleStatus).toHaveBeenCalledWith(mockAlert)
  })

  it('activates an inactive alert from the row action', async () => {
    const user = userEvent.setup()
    const inactiveAlert = { ...mockAlert, status: 'disabled' as const }
    const { onToggleStatus } = renderAlertListItem({ alert: inactiveAlert })

    expectActivateControl()
    await clickActivate(user)

    expect(onToggleStatus).toHaveBeenCalledTimes(1)
    expect(onToggleStatus).toHaveBeenCalledWith(inactiveAlert)
  })
})
