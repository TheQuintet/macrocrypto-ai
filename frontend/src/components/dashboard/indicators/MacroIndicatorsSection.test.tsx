import { cleanup, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import {
  expectCurrentView,
  expectHistoricalControls,
  renderSection,
  selectHistoryView,
} from './MacroIndicatorsSection.testHelpers'

describe('MacroIndicatorsSection', () => {
  afterEach(() => {
    cleanup()
  })

  it('starts on the current snapshot and can switch to historical', async () => {
    const user = userEvent.setup()
    renderSection(true)

    expectCurrentView()
    expect(
      screen.queryByRole('group', { name: 'Historical period' }),
    ).not.toBeInTheDocument()

    await selectHistoryView(user)

    expectHistoricalControls()
    expect(
      screen.getByRole('button', { name: '90d' }),
    ).toHaveAttribute('aria-pressed', 'true')
  })

  it('hides the view toggle when history is not enabled', () => {
    renderSection(false)

    expect(
      screen.queryByRole('group', { name: 'Indicator view' }),
    ).not.toBeInTheDocument()
  })
})
