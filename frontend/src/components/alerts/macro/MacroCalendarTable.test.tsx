import { cleanup, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import {
  clickRow,
  deleteRowAlert,
  expectRowText,
  getEventRow,
  getRowDeleteButton,
  renderMacroTable,
  toggleRowStatus,
} from './MacroCalendarTable.testHelpers'

describe('MacroCalendarTable', () => {
  afterEach(() => {
    cleanup()
  })

  it('names the event and shows whether its alert repeats', () => {
    renderMacroTable()

    expectRowText('FOMC Rate Decision', 'FOMC Rate Decision')
    expectRowText('FOMC Rate Decision', 'Alerts 1 day before')
    expectRowText('FOMC Rate Decision', 'One-time')
  })

  it('shows no lead time for an event without an alert', () => {
    renderMacroTable()

    expect(getEventRow('CPI Release')).not.toHaveTextContent('Alerts')
  })

  it('reads Active or Inactive, never Subscribed', () => {
    renderMacroTable()

    expectRowText('FOMC Rate Decision', 'Active')
    expectRowText('CPI Release', 'Inactive')
    expect(screen.queryByText(/Subscribed/)).not.toBeInTheDocument()
  })

  it('toggles an event alert from the status switch', async () => {
    const user = userEvent.setup()
    const { onSubscribeChange } = renderMacroTable()

    await toggleRowStatus(user, 'FOMC Rate Decision', 'Deactivate alert')

    expect(onSubscribeChange).toHaveBeenCalledWith('event-fed', false)
  })

  it('offers delete on every row, enabled only where an alert exists', () => {
    renderMacroTable()

    expect(getRowDeleteButton('FOMC Rate Decision')).toBeEnabled()
    expect(getRowDeleteButton('CPI Release')).toBeDisabled()
  })

  it('opens the row for editing when it is clicked', async () => {
    const user = userEvent.setup()
    const { onEdit } = renderMacroTable()

    await clickRow(user, 'FOMC Rate Decision')

    expect(onEdit).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'event-fed', event_type: 'FED' }),
    )
  })

  it('deletes the alert after confirmation, separately from pausing it', async () => {
    const user = userEvent.setup()
    const { onDelete, onSubscribeChange } = renderMacroTable()

    await deleteRowAlert(user, 'FOMC Rate Decision')

    expect(onDelete).toHaveBeenCalledWith('event-fed')
    expect(onSubscribeChange).not.toHaveBeenCalled()
  })
})
