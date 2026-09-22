import { cleanup, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import {
  clickRow,
  deleteRowAlert,
  expectRowText,
  getRowDeleteButton,
  renderMacroTable,
  toggleRowStatus,
} from './MacroCalendarTable.testHelpers'

describe('MacroCalendarTable', () => {
  afterEach(() => {
    cleanup()
  })

  it('names each subscribed event type', () => {
    renderMacroTable()

    expectRowText('Federal Reserve Meeting', 'Federal Reserve Meeting')
    expectRowText('Federal Reserve Meeting', 'HIGH')
  })

  it('leaves timing and repeat blank while the API omits them', () => {
    renderMacroTable()

    expect(screen.queryByText(/^Alerts /)).not.toBeInTheDocument()
    expect(screen.queryByText('One-time')).not.toBeInTheDocument()
  })

  it('renders only the subscriptions it is given', () => {
    renderMacroTable()

    expect(screen.getAllByRole('row')).toHaveLength(3) // header + 2 subscriptions
    expect(screen.queryByText('GDP Release')).not.toBeInTheDocument()
    expect(screen.queryByText('Employment Report')).not.toBeInTheDocument()
  })

  it('tells the reader when there are no subscriptions at all', () => {
    renderMacroTable({ subscriptions: [] })

    expect(screen.getByText('No macro subscriptions yet')).toBeInTheDocument()
  })

  it('reads Active or Inactive, never Subscribed', () => {
    renderMacroTable()

    expectRowText('Federal Reserve Meeting', 'Active')
    expectRowText('CPI Release', 'Inactive')
    expect(screen.queryByText(/Subscribed/)).not.toBeInTheDocument()
  })

  it('toggles an event alert from the status switch', async () => {
    const user = userEvent.setup()
    const { onSubscribeChange } = renderMacroTable()

    await toggleRowStatus(user, 'Federal Reserve Meeting', 'Deactivate alert')

    expect(onSubscribeChange).toHaveBeenCalledWith('subscription-fed', false)
  })

  it('offers delete on every row, enabled only where an alert exists', () => {
    renderMacroTable()

    expect(getRowDeleteButton('Federal Reserve Meeting')).toBeEnabled()
    expect(getRowDeleteButton('CPI Release')).toBeDisabled()
  })

  it('opens the row for editing when it is clicked', async () => {
    const user = userEvent.setup()
    const { onEdit } = renderMacroTable()

    await clickRow(user, 'Federal Reserve Meeting')

    expect(onEdit).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'subscription-fed', event_type: 'FED' }),
    )
  })

  it('deletes the alert after confirmation, separately from pausing it', async () => {
    const user = userEvent.setup()
    const { onDelete, onSubscribeChange } = renderMacroTable()

    await deleteRowAlert(user, 'Federal Reserve Meeting')

    expect(onDelete).toHaveBeenCalledWith('subscription-fed')
    expect(onSubscribeChange).not.toHaveBeenCalled()
  })
})
