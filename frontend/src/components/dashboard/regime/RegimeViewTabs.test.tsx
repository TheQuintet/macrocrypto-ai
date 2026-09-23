import { cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import {
  expectRegimeViewTabSelected,
  renderRegimeViewTabs,
  selectRegimeViewTab,
} from './RegimeViewTabs.testHelpers'

describe('RegimeViewTabs', () => {
  afterEach(() => {
    cleanup()
  })

  it('marks Performance as the open tab', () => {
    renderRegimeViewTabs()

    expectRegimeViewTabSelected('Performance', true)
    expectRegimeViewTabSelected('Timeline', false)
    expectRegimeViewTabSelected('Similar periods', false)
  })

  it('reports a switch to the timeline', async () => {
    const user = userEvent.setup()
    const { onChange } = renderRegimeViewTabs()

    await selectRegimeViewTab(user, 'Timeline')

    expect(onChange).toHaveBeenCalledWith('timeline')
  })

  it('reports a switch to similar periods', async () => {
    const user = userEvent.setup()
    const { onChange } = renderRegimeViewTabs()

    await selectRegimeViewTab(user, 'Similar periods')

    expect(onChange).toHaveBeenCalledWith('similarPeriods')
  })
})
