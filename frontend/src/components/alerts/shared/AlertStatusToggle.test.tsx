import { cleanup, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import {
  clickStatusSwitch,
  expectActivateSwitch,
  expectDeactivateSwitch,
  renderAlertStatusToggle,
} from './AlertStatusToggle.testHelpers'

afterEach(() => {
  cleanup()
})

describe('AlertStatusToggle', () => {
  it('shows an on switch on the Active badge', () => {
    renderAlertStatusToggle('active')

    expect(screen.getByText('Active')).toBeInTheDocument()
    expectDeactivateSwitch()
  })

  it('shows an off switch on the Inactive badge', () => {
    renderAlertStatusToggle('disabled')

    expect(screen.getByText('Inactive')).toBeInTheDocument()
    expectActivateSwitch()
  })

  it('toggles when the switch is clicked', async () => {
    const user = userEvent.setup()
    const { onToggle } = renderAlertStatusToggle('active')

    await clickStatusSwitch(user, 'active')

    expect(onToggle).toHaveBeenCalledTimes(1)
  })

  it('toggles when the badge label is clicked', async () => {
    const user = userEvent.setup()
    const { onToggle } = renderAlertStatusToggle('disabled')

    await user.click(screen.getByText('Inactive'))

    expect(onToggle).toHaveBeenCalledTimes(1)
  })
})
