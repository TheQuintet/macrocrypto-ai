import { cleanup, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  expectValidationError,
  getCreateButton,
  openAdvancedTab,
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
    expect(screen.getByRole('tab', { name: 'Alert' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('button', { name: /^Event/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Notify by' })).toHaveTextContent('1 day before')
    expect(screen.getByRole('switch', { name: 'One-time' })).toBeChecked()
    expect(screen.queryByRole('switch', { name: 'In the app' })).not.toBeInTheDocument()
    expect(getCreateButton()).toBeInTheDocument()
  })

  it('keeps notification channels on the Advanced tab', async () => {
    const user = userEvent.setup()
    renderMacroForm()

    await openAdvancedTab(user)

    expect(screen.getByRole('switch', { name: 'In the app' })).toBeInTheDocument()
    expect(screen.getByRole('switch', { name: 'Email' })).toBeInTheDocument()
    expect(screen.queryByRole('switch', { name: 'One-time' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Notify by' })).not.toBeInTheDocument()
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
    await openAdvancedTab(user)
    await toggleNamedSwitch(user, 'In the app')
    await submitMacroForm(user)

    expectValidationError('Choose a notification.')
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('summarises the selected event and submits the draft', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    renderMacroForm({ onSubmit })

    await selectMacroEvent(user, 'Federal Reserve Meeting')
    await selectNotifyBy(user, '1 hour before')

    expect(screen.getByRole('status')).toHaveTextContent(
      'Federal Reserve Meeting · high impact · 1 hour before',
    )

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
