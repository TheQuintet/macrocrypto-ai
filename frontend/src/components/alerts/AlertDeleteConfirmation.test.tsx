import { cleanup, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import { mockAlert } from './price/__tests__/testHelpers'
import {
  clickDeleteCancel,
  clickDeleteConfirm,
  expectDeleteConfirmationClosed,
  expectDeleteDetail,
  renderAlertDeleteConfirmation,
} from './AlertDeleteConfirmation.testHelpers'

describe('AlertDeleteConfirmation', () => {
  afterEach(() => {
    cleanup()
  })

  it('lists the alert details so the rule is identifiable', () => {
    renderAlertDeleteConfirmation()

    expect(screen.getByRole('heading', { name: 'Delete alert' })).toBeInTheDocument()
    expect(screen.getByText('This cannot be undone.')).toBeInTheDocument()
    expectDeleteDetail('Name', 'BTC Breakout Alert')
    expectDeleteDetail('Rule', 'BTC/USD goes above $85,000.00')
    expectDeleteDetail('Status', 'Active')
    expectDeleteDetail('Repeat', 'One-time')
    expectDeleteDetail('Notify', 'In the app')
    expectDeleteDetail('Note', 'Alert when BTC crosses above 85000')
  })

  it('stays closed when no alert is selected', () => {
    renderAlertDeleteConfirmation({ alert: null })

    expectDeleteConfirmationClosed()
  })

  it('confirms delete', async () => {
    const user = userEvent.setup()
    const { onConfirm } = renderAlertDeleteConfirmation()

    await clickDeleteConfirm(user)

    expect(onConfirm).toHaveBeenCalledTimes(1)
  })

  it('cancels without deleting', async () => {
    const user = userEvent.setup()
    const { onOpenChange, onConfirm } = renderAlertDeleteConfirmation()

    await clickDeleteCancel(user)

    expect(onOpenChange).toHaveBeenCalledWith(false)
    expect(onConfirm).not.toHaveBeenCalled()
  })

  it('omits empty name and note', () => {
    renderAlertDeleteConfirmation({
      alert: { ...mockAlert, name: '', description: null },
    })

    expect(screen.queryByText('Name')).not.toBeInTheDocument()
    expect(screen.queryByText('Note')).not.toBeInTheDocument()
    expectDeleteDetail('Rule', 'BTC/USD goes above $85,000.00')
  })
})
