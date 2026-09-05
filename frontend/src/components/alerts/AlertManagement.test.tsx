// frontend/src/components/alerts/AlertManagement.test.tsx

import { cleanup, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  chooseAlertType,
  clickNewAlert,
  expectFilterCount,
  openTab,
  renderAlertManagement,
  switchAlertTypeTo,
} from './AlertManagement.testHelpers'

vi.mock('@/hooks/alerts/usePriceAlerts', () => ({
  usePriceAlerts: vi.fn(),
}))

vi.mock('@/hooks/useBtcPriceSnapshotQuery', () => ({
  useBtcPriceSnapshotQuery: vi.fn(),
}))

vi.mock('@/api/alerts/macroAlerts', () => ({
  macroAlertApi: {
    getUpcomingEvents: vi.fn(),
    getSubscriptions: vi.fn(),
    updateSubscription: vi.fn(),
  },
}))

describe('AlertManagement', () => {
  afterEach(() => {
    cleanup()
  })

  it('counts alerts on the price tab and its filters', async () => {
    renderAlertManagement()

    expect(screen.getByRole('button', { name: 'Price Alerts (1)' })).toBeInTheDocument()
    expect(screen.getByText('1 alert configured')).toBeInTheDocument()
    expectFilterCount('All', 1)
    expectFilterCount('Active', 1)
    expectFilterCount('Inactive', 0)
  })

  it('counts events on the macro tab the same way', async () => {
    const user = userEvent.setup()
    renderAlertManagement()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Macro Events (2)' })).toBeInTheDocument()
    })

    await openTab(user, /^Macro Events/)

    expect(screen.getByText('2 events configured')).toBeInTheDocument()
    expectFilterCount('All', 2)
    expectFilterCount('Active', 0)
    expectFilterCount('Inactive', 2)
  })

  it('opens the macro edit dialog from a row click', async () => {
    const user = userEvent.setup()
    renderAlertManagement()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Macro Events (2)' })).toBeInTheDocument()
    })
    await openTab(user, /^Macro Events/)
    
    // Find and click the event name
    const eventName = screen.getByText('FOMC Rate Decision')
    await user.click(eventName)

    // Wait for the dialog to appear
    await waitFor(() => {
      // Check for the dialog by looking for the form title
      const dialogTitle = screen.getByText(/Edit.*macro/i)
      expect(dialogTitle).toBeInTheDocument()
    })

    // Verify the save button is present
    expect(screen.getByRole('button', { name: /Save changes/i })).toBeInTheDocument()
  })

  it('offers all three alert types from the plus button', async () => {
    const user = userEvent.setup()
    renderAlertManagement()

    await clickNewAlert(user)

    expect(screen.getByText('Choose alert type')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Price alert/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Macro event alert/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Prediction alert/ })).toBeInTheDocument()
  })

  it('switches a mis-picked price alert to a macro event alert', async () => {
    const user = userEvent.setup()
    renderAlertManagement()

    await clickNewAlert(user)
    await chooseAlertType(user, /Price alert/)
    expect(screen.getByText('New price alert')).toBeInTheDocument()

    await switchAlertTypeTo(user, 'Macro event alert')

    await waitFor(() => {
      expect(screen.getByText('New macro event alert')).toBeInTheDocument()
    })
    expect(screen.queryByText('New price alert')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^Event/ })).toBeInTheDocument()
  })

  it('switches back from macro to price without reopening the chooser', async () => {
    const user = userEvent.setup()
    renderAlertManagement()

    await clickNewAlert(user)
    await chooseAlertType(user, /Macro event alert/)
    await waitFor(() => {
      expect(screen.getByText('New macro event alert')).toBeInTheDocument()
    })

    await switchAlertTypeTo(user, 'Price alert')

    expect(screen.getByText('New price alert')).toBeInTheDocument()
    expect(screen.queryByText('Choose alert type')).not.toBeInTheDocument()
  })

  it('switches to prediction alert type', async () => {
    const user = userEvent.setup()
    renderAlertManagement()

    await clickNewAlert(user)
    await chooseAlertType(user, /Prediction alert/)
    
    await waitFor(() => {
      expect(screen.getByText('New prediction alert')).toBeInTheDocument()
    })
    expect(screen.queryByText('New price alert')).not.toBeInTheDocument()
    expect(screen.queryByText('New macro event alert')).not.toBeInTheDocument()
  })
})