import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import {
  expectViewNotSelected,
  expectViewSelected,
  renderViewToggle,
  selectIndicatorView,
} from './IndicatorViewToggle.testHelpers'

describe('IndicatorViewToggle', () => {
  it('marks the current view and reports the next selection', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    renderViewToggle('current', onChange)

    expectViewSelected('Current')
    expectViewNotSelected('Historical')

    await selectIndicatorView(user, 'Historical')

    expect(onChange).toHaveBeenCalledWith('historical')
  })
})
