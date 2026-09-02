import { cleanup, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  expectValidationError,
  getCreateButton,
  expectAdvancedOpen,
  getRequiredSection,
  openAdvanced,
  renderMacroForm,
  selectMacroEvent,
  selectNotifyBy,
  submitMacroForm,
  toggleNamedSwitch,
} from './MacroAlertForm.testHelpers'

describe('MacroAlertForm', () => {
  afterEach(() => {
    cleanup()
  })

  it('leads with the event and notify-by choice', () => {
    renderMacroForm()

    expect(screen.getByText('New macro event alert')).toBeInTheDocument()
    const required = within(getRequiredSection())
    expect(required.getByRole('button', { name: /^Event/ })).toBeInTheDocument()
    expect(required.getByRole('button', { name: 'Notify by' })).toHaveTextContent('1 day before')
    expect(required.getByRole('switch', { name: 'One-time' })).toBeChecked()
    expect(getCreateButton()).toBeInTheDocument()
  })

  it('folds notification channels behind Advanced', async () => {
    const user = userEvent.setup()
    renderMacroForm()

    // Collapsed content is out of the accessibility tree, not just invisible.
    expect(screen.queryByRole('switch', { name: 'In the app' })).not.toBeInTheDocument()

    await openAdvanced(user)

    expect(screen.getByRole('switch', { name: 'In the app' })).toBeVisible()
    expect(screen.getByRole('switch', { name: 'Email' })).toBeVisible()
  })

  it('requires an event before creating the alert', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    renderMacroForm({ onSubmit })

    await submitMacroForm(user)

    expectValidationError('Choose an event.')
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('requires at least one notification channel', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    renderMacroForm({ onSubmit })

    await selectMacroEvent(user, 'Federal Reserve Meeting')
    await openAdvanced(user)
    await toggleNamedSwitch(user, 'In the app')
    await submitMacroForm(user)

    expectValidationError('Choose a notification.')
    expectAdvancedOpen()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('submits the chosen event and timing', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    renderMacroForm({ onSubmit })

    await selectMacroEvent(user, 'Federal Reserve Meeting')
    await selectNotifyBy(user, '1 hour before')
    await submitMacroForm(user)

    expect(onSubmit).toHaveBeenCalledWith({
      event_type: 'FED',
      timing: '1H',
      one_time: true,
      notify_in_app: true,
      notify_email: false,
    })
  })
})
