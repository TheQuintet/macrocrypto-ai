import { cleanup, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import {
  clickDeleteCancel,
  clickDeleteConfirm,
  expectDeleteConfirmationClosed,
  expectDeleteDetail,
} from '@/components/alerts/AlertDeleteConfirmation.testHelpers'
import {
  mockPredictionAlert,
  renderPredictionAlertDeleteConfirmation,
} from './PredictionAlertDeleteConfirmation.testHelpers'

describe('PredictionAlertDeleteConfirmation', () => {
  afterEach(() => {
    cleanup()
  })

  it('lists the alert details so the rule is identifiable', () => {
    renderPredictionAlertDeleteConfirmation()

    expect(screen.getByRole('heading', { name: 'Delete alert' })).toBeInTheDocument()
    expect(screen.getByText('This cannot be undone.')).toBeInTheDocument()
    expectDeleteDetail('Name', 'Bullish Breakout')
    expectDeleteDetail('Rule', 'Prediction changes by 5% or more (24h)')
    expectDeleteDetail('Status', 'Active')
    expectDeleteDetail('Repeat', 'Repeats')
    expectDeleteDetail('Notify', 'In the app')
    expectDeleteDetail('Note', 'Strong upward movement')
  })

  it('stays closed when no alert is selected', () => {
    renderPredictionAlertDeleteConfirmation({ alert: null })

    expectDeleteConfirmationClosed()
  })

  it('confirms delete', async () => {
    const user = userEvent.setup()
    const { onConfirm } = renderPredictionAlertDeleteConfirmation()

    await clickDeleteConfirm(user)

    expect(onConfirm).toHaveBeenCalledTimes(1)
  })

  it('cancels without deleting', async () => {
    const user = userEvent.setup()
    const { onOpenChange, onConfirm } = renderPredictionAlertDeleteConfirmation()

    await clickDeleteCancel(user)

    expect(onOpenChange).toHaveBeenCalledWith(false)
    expect(onConfirm).not.toHaveBeenCalled()
  })

  it('omits empty name and note', () => {
    renderPredictionAlertDeleteConfirmation({
      alert: { ...mockPredictionAlert, name: '', description: undefined },
    })

    expect(screen.queryByText('Name')).not.toBeInTheDocument()
    expect(screen.queryByText('Note')).not.toBeInTheDocument()
    expectDeleteDetail('Rule', 'Prediction changes by 5% or more (24h)')
  })
})
